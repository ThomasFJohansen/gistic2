function save_current_figure(fname,exts)
%SAVE_CURRENT_FIGURE Save GISTIC figures using the R2026a graphics API.
% FNAME is the base filename; EXTS contains fig, png, pdf and/or eps.
%
% GISTIC software version 2.0
% Copyright (c) 2011-2017 Gad Getz, Rameen Beroukhim, Craig Mermel,
% Jen Dobson, Steve Schumacher, Nico Stransky, Mike Lawrence, Gordon Saksena
% All Rights Reserved.
% (See the accompanying LICENSE file for licensing details.)
%
% Updated from snputil/save_current_figure.m. The build stages this version
% over the upstream helper. Renderer no longer controls PRINT in R2025a+.

if nargin < 2 || isempty(exts)
    exts = {'fig'};
elseif ischar(exts) || isstring(exts)
    exts = cellstr(exts);
end

fig = gcf;
if ismember('fig',exts)
    savefig(fig,[fname '.fig']);
end
if ismember('png',exts)
    saveas(fig,[fname '.png'],'png');
end
if ismember('pdf',exts)
    print(fig,[fname '.pdf'],'-dpdf','-vector');
end
if ismember('eps',exts)
    print(fig,[fname '.eps'],'-depsc','-vector');
end
end
