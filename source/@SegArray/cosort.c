/* Modernized from snputil/@SegArray/cosort.c (cf3172b858c6ceea1688816e632228c89ba80e89).
 * Merge sorted double vectors, retaining input-list order for equal values.
 * Build with mex -R2018a; all input/output arrays are real doubles.
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
    mwSize total = 0;
    mwSize *sizes;
    mwIndex *positions;
    const mxDouble **inputs;
    mxArray *group;
    mxDouble *groups, *values = NULL, *indices = NULL;
    int i;
    mwIndex k;

    if (nlhs > 3)
        mexErrMsgIdAndTxt("gistic:cosort:outputs", "At most three outputs are supported.");

    sizes = (mwSize *)mxCalloc((mwSize)nrhs, sizeof(mwSize));
    positions = (mwIndex *)mxCalloc((mwSize)nrhs, sizeof(mwIndex));
    inputs = (const mxDouble **)mxCalloc((mwSize)nrhs, sizeof(mxDouble *));
    for (i = 0; i < nrhs; ++i) {
        if (!mxIsDouble(prhs[i]) || mxIsComplex(prhs[i]) || mxIsSparse(prhs[i]))
            mexErrMsgIdAndTxt("gistic:cosort:type", "Inputs must be full, real double arrays.");
        sizes[i] = mxGetNumberOfElements(prhs[i]);
        if (sizes[i] > ((mwSize)-1) - total)
            mexErrMsgIdAndTxt("gistic:cosort:size", "Combined input size overflows mwSize.");
        total += sizes[i];
        if ((double)total > 9007199254740991.0)
            mexErrMsgIdAndTxt("gistic:cosort:size", "Indices must be exactly representable as doubles.");
        inputs[i] = mxGetDoubles(prhs[i]);
        for (k = 0; k < sizes[i]; ++k) {
            if (!mxIsFinite(inputs[i][k]) || (k > 0 && inputs[i][k] < inputs[i][k-1]))
                mexErrMsgIdAndTxt("gistic:cosort:order", "Inputs must be finite and sorted in ascending order.");
        }
    }

    group = mxCreateDoubleMatrix(total, 1, mxREAL);
    groups = mxGetDoubles(group);
    if (nlhs >= 2) {
        plhs[1] = mxCreateDoubleMatrix(total, 1, mxREAL);
        values = mxGetDoubles(plhs[1]);
    }
    if (nlhs >= 3) {
        plhs[2] = mxCreateDoubleMatrix(total, 1, mxREAL);
        indices = mxGetDoubles(plhs[2]);
    }
    for (k = 0; k < total; ++k) {
        int selected = -1;
        mxDouble minimum = 0;
        for (i = 0; i < nrhs; ++i) {
            if (positions[i] < sizes[i]) {
                mxDouble value = inputs[i][positions[i]];
                /* Strict comparison preserves the original stable tie order. */
                if (selected < 0 || value < minimum) {
                    selected = i;
                    minimum = value;
                }
            }
        }
        ++positions[selected];
        groups[k] = (mxDouble)(selected + 1);
        if (values != NULL)
            values[k] = minimum;
        if (indices != NULL)
            indices[k] = (mxDouble)positions[selected];
    }
    mxFree(sizes);
    mxFree(positions);
    mxFree(inputs);
    if (nlhs > 0)
        plhs[0] = group;
    else
        mxDestroyArray(group);
}
