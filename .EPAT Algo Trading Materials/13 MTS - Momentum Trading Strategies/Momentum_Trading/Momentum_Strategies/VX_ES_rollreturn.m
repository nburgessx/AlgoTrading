clear;
entryThreshold=0.1;
onewaytcost=1/10000;
load('inputDataDaily_VX_20120507', 'tday', 'contracts', 'cl');

% VIX Index
[num txt]=xlsread('VIX.csv');
VIX=num(:, end);

tday_VIX=str2double(cellstr(datestr(datenum(txt(2:end, 1), 'mm/dd/yyyy' ), 'yyyymmdd')));
% tday_VIX=str2double(cellstr(datestr(datenum(txt(2:end, 1), 'mm-dd-yyyy'), 'yyyymmdd')));
[tday idx1 idx2]=intersect(tday_VIX, tday);
VIX=VIX(idx1);
VX=cl(idx2, :);

% Compare VIX with VX price at expiration
expirationIdx=isnan(fwdshift(1, VX)) & isfinite(VX);
VX_atExpire=NaN(length(VX), 1);
for t=1:length(VX)
    if (any(expirationIdx(t, :)))
        idx=find(expirationIdx(t, :));
        VX_atExpire(t)=VX(t, idx(1));
    end
end
plot(VIX, VX_atExpire, '.');

es=load('inputDataOHLCDaily_20120507', 'syms', 'tday', 'cl');
ES=es.cl(:, strcmp('ES', es.syms));
tday_ES=es.tday(:, strcmp('ES', es.syms));

[tday idx1 idx2]=intersect(tday, tday_ES);
VIX=VIX(idx1);
VX=VX(idx1, :);
ES=ES(idx2);

isExpireDate=false(size(VX));
isExpireDate=isfinite(VX) & ~isfinite(fwdshift(1, VX));

% Define front month as 40 days to 10 days before expiration
numDaysStart=30;
numDaysEnd=1;
% numDaysStart=40;
% numDaysEnd=10;

positions=[zeros(size(VX)) zeros(size(ES))];

for c=1:length(contracts)
    expireIdx=find(isExpireDate(:, c));
    if (c==1)
        startIdx=expireIdx-numDaysStart;
        endIdx=expireIdx-numDaysEnd;
    else % ensure next front month contract doesn't start until current one ends
        startIdx=max(endIdx+1, expireIdx-numDaysStart);
        endIdx=expireIdx-numDaysEnd;
    end
        
    if (~isempty(expireIdx))
        idx=startIdx:endIdx;
        %         dailyRoll=(VX(idx, c)-VIX(idx))./[expireIdx-startIdx:-1:expireIdx-endIdx]';
        dailyRoll=-(VX(idx, c)-VIX(idx))./[expireIdx-startIdx+1:-1:expireIdx-endIdx+1]';
        positions(idx(dailyRoll > entryThreshold), c)=1*0.35;
%         positions(idx(dailyRoll > entryThreshold), c)=-1;
        positions(idx(dailyRoll > entryThreshold), end)=1;
        
        % Entry level filter
        %                 positions(idx(dailyRoll > entryThreshold & VX(idx, c) > 21), c)=-1*0.3906;
        %                 positions(idx(dailyRoll > entryThreshold & VX(idx, c) > 21), end)=-1;
        
                positions(idx(dailyRoll < -entryThreshold), c)=-1*0.35;
%         positions(idx(dailyRoll < -entryThreshold), c)=1;
        positions(idx(dailyRoll < -entryThreshold), end)=-1;
        
        % Entry level filter
        %                 positions(idx(dailyRoll < -entryThreshold & VX(idx, c) < 34), c)=1*0.3906;
        %                 positions(idx(dailyRoll < -entryThreshold & VX(idx, c) < 34), end)=1;

    end
end

y=[VX*1000 ES*50];

% ret=smartsum(lag(positions).*(y-lag(y, 1)), 2)./smartsum(abs(lag(positions.*y)), 2)-...
%     onewaytcost*smartsum(abs(positions.*y-lag(positions.*y)), 2)./smartsum(abs(lag(positions.*y)), 2);
ret=smartsum(backshift(1, positions).*(y-backshift(1, y)), 2)./smartsum(abs(backshift(1, positions.*y)), 2)-...
    onewaytcost*smartsum(abs(positions.*y-backshift(1, positions.*y)), 2)./smartsum(abs(backshift(1, positions.*y)), 2);
ret(isnan(ret))=0;

% idx=find(tday >= 20080804);

% cumret=cumprod(1+ret(idx(501:end)))-1;
cumret=cumprod(1+ret)-1;
plot(cumret); % Cumulative compounded return

% fprintf(1, 'APR=%f Sharpe=%f\n', prod(1+ret(idx(501:end))).^(252/length(ret(idx(501:end))))-1, sqrt(252)*mean(ret(idx(501:end)))/std(ret(idx(501:end))));
fprintf(1, 'APR=%f Sharpe=%f\n', prod(1+ret).^(252/length(ret))-1, sqrt(252)*mean(ret)/std(ret));

[maxDD maxDDD]=calculateMaxDD(cumret);
fprintf(1, 'maxDD=%f maxDDD=%i\n', maxDD, maxDDD);
% APR=0.069065 Sharpe=1.002020
% maxDD=-0.075683 maxDDD=259
% 

% 
% If use hedge ratio [1, 1]
% APR=0.293906 Sharpe=3.263952
% maxDD=-0.035798 maxDDD=59
