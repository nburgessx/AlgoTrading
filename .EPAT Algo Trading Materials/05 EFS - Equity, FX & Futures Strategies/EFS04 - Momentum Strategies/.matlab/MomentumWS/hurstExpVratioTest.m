clear;

% 1 minute data on EURUSD
load('inputData_EURUSD_20120426', 'tday', 'hhmm', 'cl');
% load('inputDataOHLCDaily_20120517', 'tday', 'syms', 'cl');

% y=cl(:, strcmp(syms, 'ES'));

% Select the daily close at 16:59 ET.
y=cl(hhmm==1659);

plot(y);

% Find Hurst exponent

H=genhurst(log(y), 2);
fprintf(1, 'H2=%f\n', H);

% Variance ratio test from Matlab Econometrics Toolbox
[h,pValue]=vratiotest(log(y));


fprintf(1, 'h=%i\n', h); % h=1 means rejection of random walk hypothesis, 0 means it is a random walk.
fprintf(1, 'pValue=%f\n', pValue); % pValue is essentially the probability that the null hypothesis (random walk) is true.


