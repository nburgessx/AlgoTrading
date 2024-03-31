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
% expirationIdx=isnan(fwdshift(1, VX)) & isfinite(VX);
% VX_atExpire=NaN(length(VX), 1);
% for t=1:length(VX)
%     if (any(expirationIdx(t, :)))
%         idx=find(expirationIdx(t, :));
%         VX_atExpire(t)=VX(t, idx(1));
%     end
% end
% plot(VIX, VX_atExpire, '.');

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

% positions=[zeros(size(VX)) zeros(size(ES))];


VX_cont=NaN(size(VX, 1), 1); % continuous contract series
dailyRoll=NaN(size(VX_cont));

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
        if (~isempty(idx))
            dailyRoll(idx)=-(VX(idx, c)-VIX(idx))./[expireIdx-startIdx+1:-1:expireIdx-endIdx+1]';
            VX_cont(idx)=VX(idx, c);
            if (c < size(VX, 2))
                VX(:, c+1:end)=VX(:, c+1:end)+VX(idx(end), c)-VX(idx(end), c+1); % Forward adjustment to continuous contract
            end
        end
        %         positions(idx(dailyRoll > entryThreshold), c)=1*0.35;
        %         positions(idx(dailyRoll > entryThreshold), c)=-1;
        %         positions(idx(dailyRoll > entryThreshold), end)=1;
        
        % Entry level filter
        %                 positions(idx(dailyRoll > entryThreshold & VX(idx, c) > 21), c)=-1*0.3906;
        %                 positions(idx(dailyRoll > entryThreshold & VX(idx, c) > 21), end)=-1;
        
        %                 positions(idx(dailyRoll < -entryThreshold), c)=-1*0.35;
        %         positions(idx(dailyRoll < -entryThreshold), c)=1;
        %         positions(idx(dailyRoll < -entryThreshold), end)=-1;
        
        % Entry level filter
        %                 positions(idx(dailyRoll < -entryThreshold & VX(idx, c) < 34), c)=1*0.3906;
        %                 positions(idx(dailyRoll < -entryThreshold & VX(idx, c) < 34), end)=1;

    end
end

% y=[VX*1000 ES*50];

% ret=smartsum(lag(positions).*(y-lag(y, 1)), 2)./smartsum(abs(lag(positions.*y)), 2)-...
%     onewaytcost*smartsum(abs(positions.*y-lag(positions.*y)), 2)./smartsum(abs(lag(positions.*y)), 2);
% ret=smartsum(backshift(1, positions).*(y-backshift(1, y)), 2)./smartsum(abs(backshift(1, positions.*y)), 2)-...
%     onewaytcost*smartsum(abs(positions.*y-backshift(1, positions.*y)), 2)./smartsum(abs(backshift(1, positions.*y)), 2);
% ret(isnan(ret))=0;

% idx=find(tday >= 20080804);

% cumret=cumprod(1+ret(idx(501:end)))-1;
% cumret=cumprod(1+ret)-1;
% plot(cumret); % Cumulative compounded return

% fprintf(1, 'APR=%f Sharpe=%f\n', prod(1+ret(idx(501:end))).^(252/length(ret(idx(501:end))))-1, sqrt(252)*mean(ret(idx(501:end)))/std(ret(idx(501:end))));
% fprintf(1, 'APR=%f Sharpe=%f\n', prod(1+ret).^(252/length(ret))-1, sqrt(252)*mean(ret)/std(ret));
% 
% [maxDD maxDDD]=calculateMaxDD(cumret);
% fprintf(1, 'maxDD=%f maxDDD=%i\n', maxDD, maxDDD);
% APR=0.069065 Sharpe=1.002020
% maxDD=-0.075683 maxDDD=259
% 

% 
% If use hedge ratio [1, 1]
% APR=0.293906 Sharpe=3.263952
% maxDD=-0.035798 maxDDD=59

post200808=tday>=20080801;

scatter(ES(post200808), VX_cont(post200808));

if (0)
contango=dailyRoll<0;
backward=dailyRoll>0;

scatter(ES(post200808 & contango), VX_cont(post200808 & contango), 'r');
% legend('Contango');
hold on;
scatter(ES(post200808 & backward), VX_cont(post200808 & backward), 'b');
legend('Backwardation');

res_contango=ols(50*ES(post200808 & contango), [1000*VX_cont(post200808 & contango) ones(length(find(post200808 & contango)), 1)]);
res_backward=ols(50*ES(post200808 & backward), [1000*VX_cont(post200808 & backward) ones(length(find(post200808 & backward)), 1)]);
fprintf(1, 'hedge ratio (contango)=%f (backward)=%f\n', res_contango.beta(1), res_backward.beta(1));

% hedge ratio (contango)=-0.340573 (backward)=-0.294130
end

if (0)
riskOff=VIX>30;
riskOn=VIX<=30;

scatter(ES(post200808 & riskOff), VX_cont(post200808 & riskOff), 'r');
% legend('Contango');
hold on;
scatter(ES(post200808 & riskOn), VX_cont(post200808 & riskOn), 'b');
legend('riskOn');

res_riskOff=ols(50*ES(post200808 & riskOff), [1000*VX_cont(post200808 & riskOff) ones(length(find(post200808 & riskOff)), 1)]);
res_riskOn=ols(50*ES(post200808 & riskOn & isfinite(riskOn) & isfinite(VX_cont)), [1000*VX_cont(post200808 & riskOn & isfinite(riskOn)  & isfinite(VX_cont)) ones(length(find(post200808 & riskOn & isfinite(riskOn)   & isfinite(VX_cont))), 1)]);
fprintf(1, 'hedge ratio (riskOff)=%f (riskOn)=%f\n', res_riskOff.beta(1), res_riskOn.beta(1));
% hedge ratio (riskOff)=-0.314855 (riskOn)=-0.301423

hold off;
end

res=ols(50*ES(post200808 & isfinite(VX_cont) ), [1000*VX_cont(post200808  & isfinite(VX_cont)) ones(length(find(post200808 & isfinite(VX_cont) )), 1)]);
fprintf(1, 'hedge ratio =%f \n', res.beta(1));
% hedge ratio =-0.315377 

