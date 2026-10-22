function compare_mat_outputs(baseline,candidate)
% Strict full-precision check for the standalone official example (brlen=0.5).
% No tolerance or coordinate sorting; transient paths/plots are not science.
required = {'scores.0.5.mat','peak_regs.mat','wide_peak_regs.mat','perm_ads.mat'};
for k=1:numel(required)
    name=required{k}; a=fullfile(baseline,name); b=fullfile(candidate,name);
    assert(isfile(a) && isfile(b),['Missing required MAT output: ' name]);
    assert(isequaln(load(a),load(b)),['Full-precision mismatch: ' name]);
end
for name = {'orig_stats.mat','gene_stats.mat'}
    a=fullfile(baseline,name{1}); b=fullfile(candidate,name{1});
    if isfile(a) && isfile(b)
        assert(isequaln(load(a),load(b)),['Full-precision mismatch: ' name{1}]);
    else
        warning('GISTIC:Unverified','UNVERIFIED: %s not available in both outputs',name{1});
    end
end
disp('Available full-precision scientific outputs match exactly');
end
