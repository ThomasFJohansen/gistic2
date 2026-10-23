function varargout = lunique(varargin)
%LUNIQUE Preserve the legacy UNIQUE indexing used by GISTIC.

% GISTIC software version 2.0
% Copyright (c) 2011-2017 Gad Getz, Rameen Beroukhim, Craig Mermel,
% Jen Dobson, Steve Schumacher, Nico Stransky, Mike Lawrence, Gordon Saksena
% All Rights Reserved.
% (See the accompanying LICENSE file for licensing details.)

% R2026b supports 'legacy'. Keep GISTIC's historical index selection and
% row/column shapes; the default UNIQUE behavior is not interchangeable.
% make sure it's not already an option
noleg = true;
for i=1:length(varargin)
    if strcmp(class(varargin{i}),'char') && strcmp('legacy',varargin{i})
        noleg = false;
        break;
    end
end
if noleg
    % add 'legacy' option
    varargin = [varargin,'legacy'];
end
[varargout{1:nargout}] = unique(varargin{:});
