% 
% written by:
% Ernest Chan
%
% Author of “Quantitative Trading: 
% How to Start Your Own Algorithmic Trading Business”
%
% ernest@epchan.com
% www.epchan.com

clear;

load('SPX_20071123', 'tday', 'stocks', 'cl');

monthEnds=find(isLastTradingDayOfMonth(tday)); % find the indices of the days that are at month ends.
tday=tday(monthEnds);
cl=cl(monthEnds, :);

monthlyRet=(cl-lag1(cl))./lag1(cl);


positions=zeros(size(monthlyRet));

for m=14:size(monthlyRet, 1)
    [monthlyRetSorted sortIndex]=sort(monthlyRet(m-12, :));
    
    badData=find(~isfinite(monthlyRet(m-12, :)) | ~isfinite(cl(m-1, :)));
    sortIndex=setdiff(sortIndex, badData, 'stable');
    
    topN=floor(length(sortIndex)/10); % take top decile of stocks as longs, bottom decile as shorts 
    
    positions(m-1, sortIndex(1:topN))=-1;
    positions(m-1, sortIndex(end-topN+1:end))=1;       
end

ret=smartsum(lag1(positions).*monthlyRet, 2)./smartsum(abs(lag1(positions)), 2);
ret(1:13)=[];

avgannret=12*smartmean(ret);
sharpe=sqrt(12)*smartmean(ret)/smartstd(ret);

fprintf(1, 'Avg ann return=%7.4f Sharpe ratio=%7.4f\n', avgannret, sharpe);
% Output should be
% Avg ann return=-0.0129 Sharpe ratio=-0.1243
