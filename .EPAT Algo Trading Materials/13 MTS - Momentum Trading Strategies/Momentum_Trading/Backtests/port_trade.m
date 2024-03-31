%port_trade.m
clear;

load('SPX_20071123');

ret=(cl-backshift(1, cl))./backshift(1, cl); % daily returns

marketRet=smartmean(ret, 2); % equal weighted market index return

weights=-(ret-repmat(marketRet, [1 size(ret, 2)])); 

dailyret=smartsum(backshift(1, weights).*ret, 2)./smartsum(abs(backshift(1, weights)), 2);

annavgret=252*smartmean(dailyret, 1)*100

sharpe=sqrt(252)*smartmean(dailyret, 1)/smartstd(dailyret,1) % Sharpe ratio should be about 0.25

dailyret(isnan(dailyret))=0;
plot(cumprod(dailyret+1)-1);

% daily pnl with transaction costs deducted
onewaytcost=0.0005; % assume 5 basis points

% dailyretMinustcost=smartsum(backshift(1, weights).*ret-onewaytcost*abs(weights-backshift(1, weights)), 2)./smartsum(abs(backshift(1, weights)), 2);
dailyretMinustcost=dailyret-...
    smartsum(abs(weights./cl-backshift(1, weights)./backshift(1, cl)).*backshift(1, cl), 2).*onewaytcost./smartsum(abs(backshift(1, weights)), 2); % transaction costs are only incurred when the weights change

dailyretMinustcost(isnan(dailyretMinustcost))=0;
% plot(cumprod(dailyretMinustcost+1)-1);
plot(smartcumsum(dailyretMinustcost));

annavgretMinustcost=252*smartmean(dailyretMinustcost, 1)*100

sharpeMinustcost=sqrt(252)*smartmean(dailyretMinustcost, 1)/smartstd(dailyretMinustcost, 1) 

% switch to use open prices

ret=(op-backshift(1, cl))./backshift(1, cl); % daily returns

marketRet=smartmean(ret, 2); % equal weighted market index return

weights=-(ret-repmat(marketRet, [1 size(ret, 2)])); % weight of a stock is proportional to the negative distance to the market index.


dailyret=smartsum(weights.*(cl-op)./op, 2)./smartsum(abs(weights), 2);

dailyret(isnan(dailyret))=0;

plot(cumprod(dailyret+1)-1);

if (1)

annavgret=252*smartmean(dailyret, 1)*100

sharpe=sqrt(252)*smartmean(dailyret, 1)/smartstd(dailyret,1) % Sharpe ratio should be about 0.25

% daily pnl with transaction costs deducted
onewaytcost=0.0005; % assume 5 basis points

dailyretMinustcost=dailyret - ...
    smartsum(abs(weights./cl-backshift(1, weights)./backshift(1, cl)).*backshift(1, cl), 2).*onewaytcost./smartsum(abs(weights), 2); % transaction costs are only incurred when the weights change

annavgretMinustcost=252*smartmean(dailyretMinustcost, 1)*100

sharpeMinustcost=sqrt(252)*smartmean(dailyretMinustcost, 1)/smartstd(dailyretMinustcost, 1) 

% kelly optimal leverage

f=smartmean(dailyretMinustcost, 1)/smartstd(dailyretMinustcost, 1)^2

% f=40
% dailyret=f*dailyret;
% dailyretMinustcost=dailyret - ...
%     smartsum(abs(weights./cl-backshift(1, weights)./backshift(1, cl)).*backshift(1, cl), 2).*onewaytcost./smartsum(abs(weights), 2); % transaction costs are only incurred when the weights change
% dailyretMinustcost(isnan(dailyretMinustcost))=0;
% 
% APR=prod(1+dailyretMinustcost)^(252/length(dailyretMinustcost))-1

end
