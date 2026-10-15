% legacy_benchmark_values_from_miditoolbx
% Calculate the basic functions of MIDI toolbox
% for 'unit testing' or legacy comparison purposes with functions in amads
% T. Eerola, 15/2/2026

m = readmidi('sarabande.mid'); % music from amads package, note that this type 0 midi
m = m(1:10,:); % for convenience, take just 10 first notes

% Distributions
pcdist1_m = pcdist1(m);
ivdist1_m = ivdist1(m);
durdist1_m = durdist1(m);

% Summary descriptors
entropy_pcdist1_m = entropy(pcdist1(m));
nnotes_m = nnotes(m);
keymode_m = keymode(m);
kkkey_m = kkkey(m);
maxkkcc_m = maxkkcc (m);
meldistance_m = meldistance(onsetwindow(m,0,2.5,'sec'),onsetwindow(m,2.5,5,'sec'));
ambitus_m = ambitus(m);
complebm_m = complebm(m);
compltrans_m = compltrans(m); 
gradus_m = gradus(m);
notedensity_m = notedensity(m);
nPVI_m = nPVI(m); 

% Values for each note or other time-series
melcontour_m = melcontour(m,10, 'rel'); % sample 10 points
segmentgestalt_m = segmentgestalt(m);
segmentprob_m = segmentprob(m);
boundary_m =  boundary(m);
melaccent_m = melaccent(m);
melattraction_m = melattraction(m);
mobility_m = mobility(m);
narmour_m = narmour(m);
tessitura_m = tessitura(m);


%% write output to JSON file and preserve the labels
data = struct(); % initialise

% distributions
data.pcdist1 = pcdist1_m;
data.ivdist1 = ivdist1_m;
data.durdist1 = durdist1_m;

% summary descriptors
data.entropy_pcdist1 = entropy_pcdist1_m;
data.nnotes = nnotes_m;
data.keymode = keymode_m;
data.kkkey = kkkey_m;
data.maxkkcc = maxkkcc_m;

data.ambitus = ambitus_m;
data.complebm = complebm_m;
data.compltrans = compltrans_m; 
data.gradus = gradus_m;
data.meldistance = meldistance_m;
data.notedensity = notedensity_m;
data.nPVI = nPVI_m; 

% time-series
data.melcontour = melcontour_m;
data.segmentgestalt = segmentgestalt_m;
data.segmentprob = segmentprob_m;
data.boundary =  boundary_m;
data.melaccent = melaccent_m;
data.melattraction = melattraction_m;
data.mobility = mobility_m;
data.narmour = narmour_m;
data.tessitura = tessitura_m;

jsonStr = jsonencode(data);
fid = fopen('MIDI_toolbox_benchmark_sarabande.json', 'w');
fprintf(fid, '%s', jsonStr);
fclose(fid);

disp("Export complete!")
