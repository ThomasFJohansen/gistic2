function output = build_gistic(output)
%BUILD_GISTIC Build GISTIC2 for MATLAB Runtime R2026b on Linux x86-64.
% Run from a fresh MATLAB R2026b session:
%   build_gistic
% or:
%   build_gistic('/absolute/path/to/new/build-directory')
% Requires MATLAB Compiler, Statistics and Machine Learning Toolbox and a
% supported C compiler configured by mex -setup C.

root = fileparts(mfilename('fullpath'));
assert(strcmp(version('-release'),'2026b'), 'gistic:build:release', ...
    'Use MATLAB R2026b to build an application for Runtime R2026b.');
assert(strcmp(computer('arch'),'glnxa64'), 'gistic:build:platform', ...
    'Build on Linux x86-64; a Windows/macOS build cannot run on Linux.');
assert(~isempty(ver('compiler')) && license('test','Compiler'), ...
    'gistic:build:compiler', 'MATLAB Compiler is required.');
assert(~isempty(ver('stats')) && license('test','Statistics_Toolbox'), ...
    'gistic:build:stats', 'Statistics and Machine Learning Toolbox is required.');
assert(usejava('jvm'), 'gistic:build:java', ...
    'GISTIC uses Java for string matching; do not start MATLAB with -nojvm.');
cc = mex.getCompilerConfigurations('C','Selected');
assert(~isempty(cc), 'gistic:build:mex', 'Configure a supported compiler using mex -setup C.');
assert(isfile(fullfile(root,'snputil','@SegArray','SegArray.m')), ...
    'gistic:build:submodule', 'Run git submodule update --init --recursive first.');

if nargin == 0
    output = fullfile(root,'build','R2026b');
end
output = char(output);
assert(~isempty(output) && output(1) == '/', 'gistic:build:path', ...
    'The output directory must be an absolute path.');
assert(~isfolder(output) && ~isfile(output), 'gistic:build:exists', ...
    'Output already exists; choose a new directory for a clean build.');
mkdir(output);
diary(fullfile(output,'build.log'));
diaryCleanup = onCleanup(@() diary('off')); %#ok<NASGU>
disp(version); ver; disp(cc);

% Use one source tree, so duplicate utility names cannot select old helpers.
% Copy .m files only: the bundled R2014a MEX binaries must never be reused.
stage = fullfile(output,'matlab');
copy_matlab_tree(fullfile(root,'snputil'),stage);
copy_matlab_tree(fullfile(root,'source'),stage);
% The old newline.m returns literal backslash sequences and shadows MATLAB's
% newer built-in. Its only caller logs a blank line; use the built-in.
delete(fullfile(stage,'newline.m'));
classdir = fullfile(stage,'@SegArray');
for name = {'cosort','sumranges'}
    input = fullfile(root,'source','@SegArray',[name{1} '.c']);
    copyfile(input,classdir);
    mex('-R2018a','-largeArrayDims','-outdir',classdir,input);
end

oldpath = path;
pathCleanup = onCleanup(@() path(oldpath)); %#ok<NASGU>
restoredefaultpath;
addpath(stage,fullfile(root,'tests','matlab'));
test_matlab_compatibility;

% Keep the JVM for Java Hashtable and the figures needed for report export.
% Include the full utility/class tree for loaded MAT objects and dispatch.
mcc('-m','-v','-R','-nodisplay','-d',output,'-o','gp_gistic2_from_seg', ...
    '-I',stage,'-a',stage,fullfile(stage,'gp_gistic2_from_seg.m'));
assert(isfile(fullfile(output,'run_gp_gistic2_from_seg.sh')), ...
    'gistic:build:launcher', 'MATLAB Compiler did not generate its Linux launcher.');
copyfile(fullfile(root,'support','gistic2'),output);
copyfile(fullfile(root,'support','examplefiles'),fullfile(output,'examplefiles'));
copyfile(fullfile(root,'support','refgenefiles'),fullfile(output,'refgenefiles'));
copyfile(fullfile(root,'LICENSE'),fullfile(output,'LICENSE'));
copyfile(fullfile(root,'support','LICENSE.txt'),fullfile(output,'LICENSE.txt'));
fid = fopen(fullfile(output,'MATLAB_VERSION.txt'),'w');
assert(fid >= 0, 'gistic:build:metadata', 'Cannot write MATLAB_VERSION.txt.');
fileCleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n%s\n%s\n',version,version('-release'),version('-description'));
fprintf('Built GISTIC2 in %s\n',output);
fprintf('Use MATLAB Runtime R2026b at the same or newer update level.\n');
end

function copy_matlab_tree(from,to)
if ~isfolder(to)
    mkdir(to);
end
entries = dir(from);
for k = 1:numel(entries)
    name = entries(k).name;
    if startsWith(name,'.')
        continue;
    end
    if entries(k).isdir
        copy_matlab_tree(fullfile(from,name),fullfile(to,name));
    elseif endsWith(name,'.m')
        copyfile(fullfile(from,name),fullfile(to,name),'f');
    end
end
end
