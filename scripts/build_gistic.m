function build_gistic
% Stages source and rebuilds every bundled MEX for the selected MATLAB.
repo = getenv('GISTIC_BUILD_REPO');
out = getenv('GISTIC_BUILD_OUTPUT');
assert(isunix && strcmp(computer('arch'),'glnxa64'),'Linux x86-64 is required');
assert(~isempty(ver('compiler')) && license('test','Compiler'),'MATLAB Compiler is required');
assert(~isempty(ver('stats')) && license('test','Statistics_Toolbox'),'Statistics Toolbox is required');
diary(fullfile(out,'build.log'));
cleanup = onCleanup(@() diary('off')); %#ok<NASGU>
disp(version); ver; disp(version('-blas')); disp(version('-lapack'));
cc = mex.getCompilerConfigurations('C','Selected');
assert(~isempty(cc),'Configure a supported C compiler with mex -setup C');
disp(cc);
stage = fullfile(out,'build-source'); mkdir(stage);
copyfile(fullfile(repo,'source'),fullfile(stage,'source'));
copyfile(fullfile(repo,'snputil'),fullfile(stage,'snputil'));
oldmex = dir(fullfile(stage,'**','*.mex*'));
for k=1:numel(oldmex)
    delete(fullfile(oldmex(k).folder,oldmex(k).name));
end
src = fullfile(stage,'source');
util = fullfile(stage,'snputil');
addpath(src,util);
mexdir = fullfile(util,'@SegArray');
for name = {'cosort','sumranges'}
    mex('-R2017b','-largeArrayDims','-outdir',mexdir,fullfile(mexdir,[name{1} '.c']));
end
addpath(fullfile(repo,'tests','matlab'));
test_segarray;
mcc('-m','-v','-R','-nodisplay','-d',out,'-o','gp_gistic2_from_seg', ...
    '-I',src,'-I',util,'-a',util,fullfile(src,'gp_gistic2_from_seg.m'));
[major,minor] = mcrversion;
fid = fopen(fullfile(out,'runtime-abi.txt'),'w');
assert(fid>=0); fprintf(fid,'%d.%d\n',major,minor); fclose(fid);
fid = fopen(fullfile(out,'matlab-version.txt'),'w');
assert(fid>=0); fprintf(fid,'%s\n%s\n',version,version('-release')); fclose(fid);
end
