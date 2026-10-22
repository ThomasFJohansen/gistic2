function test_segarray
% Exercises valid SegArray operations, including BLAS-backed nnz and both MEXes.
x = [0 1 2;0 1 2;3 1 0;3 4 0;3 4 5];
s = SegArray(x);
assert(isequal(full(s),x));
assert(nnz(s)==nnz(x));
assert(isequal(full(sum(s,1)),sum(x,1)));
assert(isequal(full(sum(s,2)),sum(x,2)));
assert(isequal(full(s([5 1 3],[3 1])),x([5 1 3],[3 1])));
s(2:4,2)=7; x(2:4,2)=7;
assert(isequal(full(s),x));
[g,v,i] = SegArray.cosort([1;3;3],[2;3;5]);
assert(isequal(g,[1;2;1;1;2;2]));
assert(isequal(v,[1;2;3;3;3;5]));
assert(isequal(i,[1;1;2;3;2;3]));
assert(isequal(SegArray.sumranges([1;2],[3;4],[2;5],4),[2;7;7;5]));
assert(isequal(SegArray.sumranges([],[],[],4),zeros(4,1)));
disp('SegArray valid-input regression passed');
end
