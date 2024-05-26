clear;
lookback1=30;
lookback2=40;


load('inputDataOHLCDaily_20120504', 'syms', 'tday', 'cl');
idx=strcmp('CL', syms);
cl=cl(:, idx);
tday=tday(:, idx);

% longs= cl < lag(cl, lookback1) & cl > lag(movingAvg(cl, lookback2), 1);
% shorts=cl > lag(cl, lookback1) & cl < lag(movingAvg(cl, lookback2), 1);

% longs=  cl > lag(cl, lookback2);
% shorts= cl < lag(cl, lookback2);
longs= cl < backshift(lookback1, cl) & cl > backshift(lookback2, cl);
shorts=cl > backshift(lookback1, cl) & cl < backshift(lookback2, cl);
% longs= cl < lag(cl, lookback1) ;
% shorts=cl > lag(cl, lookback1) ;

positions=zeros(size(cl));
positions(longs)=1;
positions(shorts)=-1;


% ret=lag(positions, 1).*(cl-lag(cl, 1))./lag(cl, 1);
ret=backshift(1, positions).*(cl-backshift(1, cl))./backshift(1, cl);
ret(isnan(ret))=0;

% plot(cumprod(1+ret)-1, 'r'); % Cumulative compounded return
cumret=cumprod(1+ret)-1;

% dateaxis('X', 12, datenum(num2str(tday(1)), 'yyyymmdd'));
plot(datetime(tday, 'ConvertFrom', 'yyyyMMdd'), cumret, 'r');
hold on;
fprintf(1, 'APR=%f Sharpe=%f\n', prod(1+ret).^(252/length(ret))-1, sqrt(252)*mean(ret)/std(ret));
% APR=0.117600 Sharpe=1.100368

% Momentum only
longs= cl > backshift(lookback2, cl);
shorts=cl < backshift(lookback2, cl);
positions=zeros(size(cl));
positions(longs)=1;
positions(shorts)=-1;
ret=backshift(1, positions).*(cl-backshift(1, cl))./backshift(1, cl);
ret(isnan(ret))=0;

% plot(cumprod(1+ret)-1, 'g'); % Cumulative compounded return
cumret=cumprod(1+ret)-1;
plot(datetime(tday, 'ConvertFrom', 'yyyyMMdd'), cumret, 'g');

% Reversal only
longs= cl < backshift(lookback1, cl);
shorts=cl > backshift(lookback1, cl);
positions=zeros(size(cl));
positions(longs)=1;
positions(shorts)=-1;
ret=backshift(1, positions).*(cl-backshift(1, cl))./backshift(1, cl);
ret(isnan(ret))=0;

cumret=cumprod(1+ret)-1;
plot(datetime(tday, 'ConvertFrom', 'yyyyMMdd'), cumret, 'k');

% plot(cumprod(1+ret)-1, 'k'); % Cumulative compounded return

legend('Combo', 'Momentum', 'Reversal');

longs= cl < backshift(lookback1, cl) | cl > backshift(lookback2, cl);
shorts=cl > backshift(lookback1, cl) | cl < backshift(lookback2, cl);
% longs= cl < lag(cl, lookback1) ;
% shorts=cl > lag(cl, lookback1) ;

positions=zeros(size(cl));
positionsL=zeros(size(cl));
positionsS=zeros(size(cl));
positionsL(longs)=1;
positionsS(shorts)=-1;
positions=positionsL+positionsS;


% ret=lag(positions, 1).*(cl-lag(cl, 1))./lag(cl, 1);
ret=backshift(1, positions).*(cl-backshift(1, cl))./backshift(1, cl);
ret(isnan(ret))=0;

plot(cumprod(1+ret)-1, 'c'); % Cumulative compounded return
legend('ComboAND', 'Momentum', 'Reversal', 'ComboOR');

hold off;
