clear;
lookback=252; % use lookback days as estimation (training) period for determining factor exposures.
numFactors=5;
topN=50; % for trading strategy, long stocks with topN expected 1-day returns.
onewaytcost=0/10000;

 load('IJR_20080114.mat');
% test on SP600 smallcap stocks. (This MATLAB binary input file contains tday, stocks, op, hi, lo, cl arrays.

mycls=fillMissingData(cl);

positionsTable=zeros(size(cl));

dailyret=(mycls-backshift(1, mycls))./backshift(1, mycls); % note the rows of dailyret are the observations at different time periods

end_index = length(tday);


for t=lookback+2:end_index
    
    R=dailyret(t-lookback:t-1,:)'; % here the columns of R are the different observations.
    
    hasData=find(all(isfinite(R), 2)); % avoid any stocks with missing returns
    
    R=R(hasData, :);
    [PCALoadings,PCAScores,PCAVar] = pca(R);
    X = PCAScores(:,1:numFactors);
    y = dailyret(t, hasData)';
    Xreg = [ones(size(X, 1), 1) X];
    [b,sigma]=mvregress(Xreg,y);
    pred = Xreg*b;
    Rexp=sum(pred,2); % Rexp is the expected return for next period assuming factor returns remain constant.
    [foo idxSort]=sort(Rexp, 'ascend');
    
    positionsTable(t, hasData(idxSort(1:topN)))=-1; % short topN stocks with lowest expected returns
    positionsTable(t, hasData(idxSort(end-topN+1:end)))=1; % buy topN stocks with highest  expected returns
end
ret=smartsum(backshift(1, positionsTable).*dailyret-onewaytcost*abs(positionsTable-backshift(1, positionsTable)), 2)./smartsum(abs(backshift(1, positionsTable)), 2); % compute daily returns of trading strategy
fprintf(1, 'AvgAnnRet=%f Sharpe=%f\n', smartmean(ret,1)*252, sqrt(252)*smartmean(ret,1)/smartstd(ret,1));
% AvgAnnRet=0.020205 Sharpe=0.211120
