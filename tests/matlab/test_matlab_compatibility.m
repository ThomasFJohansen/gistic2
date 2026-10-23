function test_matlab_compatibility
% Small migration checks run by build_gistic after rebuilding the MEX files.
% These do not replace an end-to-end comparison of scientific output.

% Preserve UNIQUE's last-occurrence indices and legacy output orientation.
x = [3 1 3 2 1];
[u,i,j] = lunique(x);
assert(isequal(u,[1 2 3]) && isequal(i,[5 4 3]) && isequal(j,[3 1 3 2 1]));
for input = {x,x',[],[NaN 1 NaN],{'b','a','b'}}
    [u,i,j] = lunique(input{1});
    [v,k,l] = unique(input{1},'legacy');
    assert(isequaln(u,v) && isequal(i,k) && isequal(j,l));
end
[u,i,j] = lunique([2 1;1 2;2 1],'rows');
[v,k,l] = unique([2 1;1 2;2 1],'rows','legacy');
assert(isequal(u,v) && isequal(i,k) && isequal(j,l));

% Native merge: duplicates must prefer earlier input lists.
[g,v,i] = SegArray.cosort([1;3;3;8],[1;3;4],[]);
assert(isequal(g,[1;2;1;1;2;2;1]));
assert(isequal(v,[1;1;3;3;3;4;8]));
assert(isequal(i,[1;1;2;3;2;3;4]));
assert(isempty(SegArray.cosort([],[])));
assert(isequal(SegArray.cosort(1,1),[1;2]));
SegArray.cosort([1;2]); % no output must also be safe
must_error(@() SegArray.cosort(sparse(1)), 'gistic:cosort:type');
must_error(@() SegArray.cosort(1i), 'gistic:cosort:type');
must_error(@() SegArray.cosort([2;1]), 'gistic:cosort:order');

% Native addition: retain overlap order, reversed empty ranges and NaNs.
actual = SegArray.sumranges([1;2;3],[2;4;2],[2;-1;100],4);
assert(isequal(actual,[2;1;-1;-1]));
assert(isempty(SegArray.sumranges([],[],[],0)));
assert(isequaln(SegArray.sumranges([1;2],[1;2],[NaN;3],2),[NaN;3]));
SegArray.sumranges(1,1,2,1);
must_error(@() SegArray.sumranges(0,1,1,2), 'gistic:sumranges:index');
must_error(@() SegArray.sumranges(1,3,1,2), 'gistic:sumranges:index');
must_error(@() SegArray.sumranges(1,1,1,-1), 'gistic:sumranges:size');
must_error(@() SegArray.sumranges(single(1),1,1,1), 'gistic:sumranges:type');

% Exercise the SegArray paths that formerly used nonscalar colon operands.
A = [1 5;1 5;3 2;3 2;4 2;4 7];
S = SegArray(A);
assert(isequal(full(SegArray(S)),A)); % anneal
assert(isequal(full(reshape(S,3,4)),reshape(A,3,4)));
assert(isequal(full(S(:,[2 1 2])),A(:,[2 1 2]))); % column swizzle
assert(isequal(full(S([6 1 3],:)),A([6 1 3],:)));
[actual,order] = sort(S,1);
[expected,expectedOrder] = sort(A,1);
assert(isequal(full(actual),expected) && isequal(order,expectedOrder));
assert(isequal(full(repmat(S,2,2)),repmat(A,2,2)));
assert(isequal(repmat(3,SegArray(2),SegArray(2)),repmat(3,2,2)));
R = SegArray.fromSegments([1;3],[2;4],[1;2],[5;7],0,4,2);
assert(isequal(full(R),[5 0;5 0;0 7;0 7]));
actual = addSegments(S,[1;2],[3;5],[1;2],[2;-1]);
expected = A;
expected(1:3,1) = expected(1:3,1)+2;
expected(2:5,2) = expected(2:5,2)-1;
assert(isequal(full(actual),expected));
D.dat = A;
D.chrn = (1:6)';
D.extra = (11:16)';
D = reorder_D_rows(D,[6 2]);
assert(isequal(D.dat,A([6 2],:)) && isequal(D.extra,[16;12]));

% Keep class dispatch for missing-data reductions rather than replacing
% nanmean/nanmedian indiscriminately with unsupported SegArray options.
A(2,1) = NaN;
S = SegArray(A);
assert(isequaln(full(nanmean(S,1)),nanmean(A,1)));
assert(isequaln(full(nanmedian(S,1)),nanmedian(A,1)));

% Exercise Java matching retained by the compiler (no -nojvm).
[~,mi,mj] = match_string_sets_hash({'b';'a';'b'},{'a';'b'});
assert(isequal(sortrows([mi(:),mj(:)]),[1 2;2 1;3 2]));

% Modern handles, deleted axes, missing patches, and all report formats.
fig = figure('Visible','off');
figureCleanup = onCleanup(@() close(fig)); %#ok<NASGU>
grid = make_subplotgrid([1 1],1,[1 1 1],[1 1],0.1,0.1);
[h,grid] = subplotgrid(grid,1,1);
[h2,grid] = subplotgrid(grid,1,1);
assert(isequal(h,h2) && isgraphics(h,'axes'));
delete(h);
[h,grid] = subplotgrid(grid,1,1); %#ok<ASGLU>
assert(isgraphics(h,'axes'));
axis([0 4 0 2]);
p = add_patches([1 NaN 2],[1 0 0;0 0 1],0.4,0.2,0.1,0.1);
assert(isgraphics(p(1)) && ~isgraphics(p(2)) && isgraphics(p(3)));
assert(isempty(draw_names_box({},'ver',10)));
assert(all(isgraphics(draw_names_box({'a';'b'},'ver',10))));
draw_spaced_text({'a';'b'},[1;2],0,3,0.1,0.3,0.32,0.5,0,[]);
folder = tempname;
mkdir(folder);
folderCleanup = onCleanup(@() rmdir(folder,'s')); %#ok<NASGU>
base = fullfile(folder,'graphics');
save_current_figure(base,{'pdf','eps','png','fig'});
for ext = {'pdf','eps','png','fig'}
    file = dir([base '.' ext{1}]);
    assert(~isempty(file) && file.bytes > 0);
end
disp('MATLAB migration checks passed.');
end

function must_error(action,id)
try
    action();
catch err
    assert(strcmp(err.identifier,id), 'Unexpected error: %s',err.identifier);
    return;
end
error('gistic:test:missingError','Expected error %s was not raised.',id);
end
