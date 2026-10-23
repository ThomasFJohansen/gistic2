/* Modernized from snputil/@SegArray/sumranges.c (cf3172b858c6ceea1688816e632228c89ba80e89).
 * Add V(i) to output positions B(i):E(i), in the original accumulation order.
 * Build with mex -R2018a; indices and output size must be finite integers.
 *
 * GISTIC software version 2.0
 * Copyright (c) 2011-2017 Gad Getz, Rameen Beroukhim, Craig Mermel,
 * Jen Dobson, Steve Schumacher, Nico Stransky, Mike Lawrence, Gordon Saksena
 * All Rights Reserved. See the accompanying LICENSE file.
 */
#include "mex.h"
#include <math.h>

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{
    const mxDouble *starts, *ends, *values;
    mxDouble requested;
    mxArray *output;
    mxDouble *result;
    mwSize count, length;
    mwIndex i;
    int arg;

    if (nrhs != 4 || nlhs > 1)
        mexErrMsgIdAndTxt("gistic:sumranges:arity", "Four inputs and at most one output are required.");
    for (arg = 0; arg < 4; ++arg) {
        if (!mxIsDouble(prhs[arg]) || mxIsComplex(prhs[arg]) || mxIsSparse(prhs[arg]))
            mexErrMsgIdAndTxt("gistic:sumranges:type", "Inputs must be full, real double arrays.");
    }
    if (mxGetNumberOfElements(prhs[3]) != 1)
        mexErrMsgIdAndTxt("gistic:sumranges:size", "Output size must be a scalar.");
    requested = mxGetScalar(prhs[3]);
    if (!mxIsFinite(requested) || requested < 0 || requested != floor(requested) ||
        requested >= (double)((mwSize)-1) || requested > 9007199254740991.0)
        mexErrMsgIdAndTxt("gistic:sumranges:size", "Output size must be a representable nonnegative integer.");
    length = (mwSize)requested;
    count = mxGetNumberOfElements(prhs[0]);
    if (mxGetNumberOfElements(prhs[1]) != count || mxGetNumberOfElements(prhs[2]) != count)
        mexErrMsgIdAndTxt("gistic:sumranges:length", "B, E and V must have equal lengths.");
    starts = mxGetDoubles(prhs[0]);
    ends = mxGetDoubles(prhs[1]);
    values = mxGetDoubles(prhs[2]);
    for (i = 0; i < count; ++i) {
        if (!mxIsFinite(starts[i]) || !mxIsFinite(ends[i]) ||
            starts[i] != floor(starts[i]) || ends[i] != floor(ends[i]) ||
            starts[i] < 1 || starts[i] > requested || ends[i] < 0 || ends[i] > requested)
            mexErrMsgIdAndTxt("gistic:sumranges:index", "Range indices are outside the output or are not integers.");
    }
    output = mxCreateDoubleMatrix(length, 1, mxREAL);
    result = mxGetDoubles(output); /* mxCreateDoubleMatrix initializes to zero. */
    for (i = 0; i < count; ++i) {
        mwIndex j;
        /* Preserve MATLAB B:E semantics, including empty reversed ranges. */
        for (j = (mwIndex)starts[i] - 1; j < (mwIndex)ends[i]; ++j)
            result[j] += values[i];
    }
    if (nlhs > 0)
        plhs[0] = output;
    else
        mxDestroyArray(output);
}
