#!/usr/bin/perl

use CGI::Carp qw(fatalsToBrowser);
use strict;
use CGI;
use POSIX;
use Data::Dumper;
use DBI;
use WebCqp::Query_dev; # this is the modified version of the module
use File::Copy;
use Text::Iconv;
use Encode;




# if Glossa.pm is not installed in the system directories
# (you can use this, for example, if you are making changes, 
# or if you don't have access to the root account)          
use lib ('/home/httpd/html/glossa/pm/');

use Glossa_old;

require 'shared.pl';

##                                        ##
##             0. Initialization          ##
##                                        ##



## get cgi input

# All the input from the user (form data) is converted to a hash, which
# is sendt to the Glossa module for further processing, since some 
# of the information is stored as "_"-delimited names and values.
# It is returned as a new hash "%in" containing all the input
# as a hash of hashes, which can be called like this:
# $corpus = $in{'query'}->{'corpus'}->[0];

my $cgi = CGI->new;

# FIXME: this should be done in module

my $google = 0;

my $test = 1;
#my $utskrift;

my $atttype = $cgi->param('atttype');

#<scandiasyn>

my $parallel = 0;
if($atttype eq 'x'){$parallel = 2; $atttype = 0}
#</scandiasyn>

my %cgi_hash;
my @prms = $cgi->param();
foreach my $p (@prms) {
    my $p2 = $p;
    $p2 =~ s/\[\]$//;
    if($p eq "tid"){print "";}
    my @vals = $cgi->param($p);

#    if($test){$utskrift = sprintf $p . " - " . @vals . "<br />\n";}

    $cgi_hash{$p2}=\@vals;
}

# This functions converts the cgi input to a hash, based on underscores
# (_) in the parameter names. This is a bit unintuitive, and is a key point
# to grasp.
# FIXME: examples
my $in = Glossa::create_cgi_hash2(\%cgi_hash);
my %in = %$in;


my $debug = 0;

my $CORPUS = $in{'query'}->{'corpus'}->[0];
my $user = $ENV{'REMOTE_USER'};
my $display_struct = CGI::param('structDisplay');
my $player = CGI::param('player');

# read main configuration file
my $conf_path_fn = "paths.conf";
my %base_conf = readConfigFile($conf_path_fn);

# read corpus configuration file
my $conf_corpus_fn = $base_conf{'config_dir'} . "/" . $CORPUS . "/cgi.conf";
my %conf = readConfigFile($conf_corpus_fn);

# update configuration with information passed in the http request
$conf{'base_corpus'}=$CORPUS;
$conf{'htmlRoot'}='/' . getRootURIPath() . "/glossa";
$conf{'cgiRoot'}='/cgi-bin/' . getRootURIPath() . '/glossa';

my $corpus_mode = $conf{'corpus_mode'};

my $speech_corpus = 0;

if($corpus_mode eq 'speech'){
    $speech_corpus = 1;
}

# multitag file
my $file = $conf{'config_dir'} . "/" . $CORPUS . "/multitags.dat";
my %multitags;
open (M, $file);
while (<M>) {
    chomp;
    next if (/^#/);
    s/\s*$//;
    my ($a,$b,$c)=split(/\t/);
    next unless ($a and $b and $c);
    $multitags{$a}->{$b}=$c;
}
close M;

# language file
my $lang_file = $conf{'config_dir'} . "/lang/" . $conf{'lang'} . ".dat";

   

my %lang;

open (LANG, $lang_file);
while (<LANG>) {
    chomp;
    s/\s*$//;
    my ($k,$v)=split(/\s*=\s*/);
    $lang{$k}=$v;
}
close LANG;


## start the HTTP session and HTML file
print "Content-type: text/html; charset=$conf{'charset'}\n\n";

print "<html>\n<head>\n<link rel=\"shortcut icon\" href=\"/favicon.ico\" type=\"image/ico\" />\n<title>$lang{'title'}</title>\n" .
      "<link href=\"", $conf{'htmlRoot'}, "/html/tags.css\" rel=\"stylesheet\" type=\"text/css\"></link>\n";

    if($CORPUS eq 'mak') {
	print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=ISO-8859-5">';
    }
    elsif($CORPUS eq 'latvian') {
	print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=CP1257">';
    }
    elsif($CORPUS eq 'run') {
	print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">';
    }
    elsif($CORPUS eq 'quran_mono') {
	print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">';
    }
    elsif($CORPUS eq 'quran_parallel') {
	print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">';
    }
    elsif($CORPUS eq 'uncorpora') {
	print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">';
    }
    elsif($CORPUS eq 'japanese_test') {
	print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">';
    }
    elsif($CORPUS eq 'japanese_s_test') {
	print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">';
    }


# Javascript programs used in displaying results.
print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/wait.js\"></script>\n";
print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/", $CORPUS, ".conf.js\"></script>\n";
print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/reslist.js\"></script>\n";
print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/showtag.js\"></script>\n";
my $video_scripts = <<STOP;
   <link rel="stylesheet" href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.6/themes/base/jquery-ui.css" type="text/css" media="all" />
   <link rel="stylesheet" href="http://static.jquery.com/ui/css/demo-docs-theme/ui.theme.css" type="text/css" media="all" />
   <link rel="stylesheet" type="text/css" href="$conf{'htmlRoot'}/player/player.css" />
   <link href="$conf{'htmlRoot'}/html/tags.css" rel="stylesheet" type="text/css" />
   <script type='text/javascript' src='$conf{'htmlRoot'}/player/player.ajax.js'></script>
   <script language="JavaScript" src="$conf{'htmlRoot'}/js/showtag.js" ></script>
   <script type='text/javascript' src='$conf{'htmlRoot'}/js/jquery/jquery-1.4.3.min.js'></script>
   <script type='text/javascript' src='$conf{'htmlRoot'}/js/jquery/jquery-ui-1.8.6.custom.min.js'></script>
   <script type='text/javascript' src='$conf{'htmlRoot'}/player/slider.js'></script>
   <script type='text/javascript'>var player;</script>
STOP

my $googletrans = <<STOP;
<script type="text/javascript" src="http://www.google.com/jsapi"></script>
<script type="text/javascript">

google.load("language", "1");

function translate(node, text) {
  text = text.replace(/_/, " ");
  google.language.detect(text, function(result) {
    if (!result.error && result.language) {
      google.language.translate(text, result.language, "en",
                                function(result) {
        if (result.translation) {
	    node.innerHTML = result.translation;
	    node.innerHTML += " <font size='-2'>(google)</font>"; //"&nbsp;<img src='$conf{'htmlRoot'}/html/img/google-g-icon-16.png'>";
        }
        else{ node.innerHTML = 'No translation available' }
      });
    }
  });
}

var globalNodeVar;
function appendTranslateScript(node,text){
    globalNodeVar = node;
    var newScript = document.createElement('script');
    newScript.type = 'text/javascript';
    var sourceText = encodeURI(text); // seems to work better than encode() function
    var source = 'https://www.googleapis.com/language/translate/v2?key=AIzaSyALLIemzcsdQYpyqxAE5k3V7luZ73P5SOQ&target=en&callback=translateText&q=' + sourceText;
    newScript.src = source;
    document.getElementsByTagName('head')[0].appendChild(newScript);
}
function translateText(response){
    globalNodeVar.innerHTML = response.data.translations[0].translatedText;
    globalNodeVar.innerHTML += " <font size='-2'>(google)</font>"; //"&nbsp;<img src='$conf{'htmlRoot'}/html/img/google-g-icon-16.png'>";
    globalNodeVar = 0;
}


function translate2(text) {
  google.language.detect(text, function(result) {
   if (!result.error && result.language) {
      google.language.translate(text, result.language, "en",
                                function(result) {
        if (result.translation) {
          return result.translation;
        }
	return "No translation available.";
      });
    }
  });
}
</script>
STOP

#print TEMP "\n\nZee Root->" . $conf{'htmlRoot'} . "\n";

#close TEMP;

my $style = <<STYLE;
<style>
div.inspect{

	top: 0px;
	left:0px;
	padding: 5px;
	border: 0px solid #000;
	background: #fff;
	width: 100%;
        height: 340px;
	display: none;
}
</style>
STYLE

if($speech_corpus){print $video_scripts;}
print "\n$googletrans\n\n";
print "$style\n</head>\n<body>\n";

#print "<div>Due to recent security updates some users may experience problems viewing video on Windows PCs. We are looking into this and apologize for the inconvenience.</div>";
#print "<div>Due to recent security updates some users may experience problems viewing video with Quicktime. These users should contact Tekstlaboratoriet at tekstlab-post\@iln.uio.no.</div>";
#print $utskrift;
foreach my $p (@prms) {
#    if($p eq "tid"){print "!!!";}
    my @vals = $cgi->param($p);

    if(0){print $p." - "; foreach my $val (@vals){ print $val . "<br />\n";}}

}

my $media_div = <<STOP;
<div id="inspector" class="inspect">
    <div id="playerpos" style="top:0px;left:0px;position:absolute;width:400px;height:300px">
        <div id='player' class='video'>Loading player...</div>
    </div>
    <div class='console' id="ctrl">
        <div class="demo" id="holder">
           <div id="slider-range"></div>
           <div style="float:left;width:24px;position:absolute;left:6px;bottom:3;"><input type="text" id="amountl" style="border:0; color:#ff2200; font-weight:bold;width:24px;background:#000;" /></div>
           <div style="float:left;position:absolute;left:194px;width:12px;height:16px;cursor:pointer;border:0px solid #f00;bottom:3;" id="play" ><img src="$conf{'htmlRoot'}/player/Button-Play-icon.png" style="align:bottom;" /></div>
           <div style="float:right;width:24px;position:absolute;left:378px;bottom:3;"><input type="text" id="amountr" style="border:0; color:#ff2200; font-weight:bold;background:#000;width:20px;" /></div>
       </div>
    </div>
    <div id='scrollbox'></div>
    <div id='pops'></div>
</div> 
    <div style="z-index: 1;" id='timecodes'></div>
STOP

    if($speech_corpus){
	if($player eq 'qt'){
#"  <span onclick=\"document.getElementById('inspector').style.display='block';\" style=\"cursor: pointer;\">[0]</span>\n" .

print "  <div id=\"inspector\" class=\"inspect\">\n" .
      "    <iframe frameborder='0' width='100%' height='100%' id=\"movie_frame\"></iframe>\n" .
      "    <div style=\"position: relative; left: 0px; top: 0px; cursor: pointer\" onclick=\"document.getElementById('inspector').style.display='none';\">\n" .
      "      <img alt=\"[x]\" src=\"" . $conf{'htmlRoot'}  . "html/img/close.png\" />\n" . 
      "    </div>\n" .
      "  </div>\n<br />\n";
	}
	else{
	    print $media_div;
	}
}
print "  <div id=\"body\">\n";

#print "<script>alert('".$lang_file."')</script>";
# FIXME: temporary message
#if ($CORPUS eq 'test') {
    #print "<script language=\"JavaScript\">stopWait()</script>";
    #print "<strong><font color='red'>Sorry!<br><br>We don't currently have a completely free corpus 
#that we can show results from. If you would like to know more about Glossa, and actually see how it displays results, please contact lars.nygaard\@iln.uio.no</strong><font color='grey'>'";
    #die;
#}



## for debugging
if ($debug) {
    print "L: $conf_corpus_fn<br>";
    print "<pre>";
    print Dumper %in;
    print "</pre>";
}
# more debugging
if($debug){
    my @prms = $cgi->param();
    foreach my $prm (@prms){
	my @vals = $cgi->param($prm);
	my $elts = @vals;
	if($vals[0]){
	    print "$prm ($elts): ";
	    foreach my $val (@vals){ print "$val, " }
	    print "<br />";
	}
    }
}

# group file; for corpora with restricted access (in addition to 
# the .htaccess restrictions). Space-separated list of allowed users.
if ($conf{'groupfile'}) {
    unless (-e $conf{'groupfile'}) { die("group file specified, but not found ($conf{'groupfile'})"); }
    my %allowed_users;
    open (H, $conf{'groupfile'});
    while (<H>) {
	next if (/^\s*#/);
	next if (/^\s*\n/);
	chomp;
	foreach my $u (split(/ +/, $_)) {
	    $allowed_users{$u}=1;
	}
    }
    unless ($allowed_users{$user}) {
	die("You do not have access to this corpus.");
    }
}


# set up charset conversion

#my $iconv;
#my $iconvr;
#if ($conf{'charsetfrom'}) {
#    $iconv= Text::Iconv->new($conf{'charsetfrom'}, $conf{'charset'});
#    $iconvr= Text::Iconv->new($conf{'charset'}, $conf{'charsetfrom'});
#} 


## Set query id
# This id is used to identify the files resulting from a query, so 
# they can be processed by other functions (collocations, annotation etc.)
my $starttime=time();
    my $rand = int(rand 100000);
$conf{'query_id'} = $starttime . "_" . $rand;

#print "ID: $conf{'query_id'}<br>";

## open log file
#open (LOG, ">>$conf{'logfile'}");
#print LOG "BEGYNNER QUERY\n";


## turn off buffering; just a trick to display stuff more quickly
select(STDOUT);
$|=1;


## initialize MySQL session
my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1});


## define some entities
my $apostr = chr(0x60);




##                                        ##
##             1. Build query             ##
##                                        ##

# hashes for storing sub-queries
my %corpora;                           
my %aligned_corpora;                   
my %aligned_corpora_opt;               # "opt" = optional

my $base_corpus;                       # name of base corpus (i.e. non-aligned)
my $aligned;                           # boolean: indicate if there are restrictions on aligned corpora
my $phrases=$in{'phrase'}->{'number'}; # the number of phrases (i.e. "rows" in the interface)

my @token_freq;


## Loop through all the phrases
# This is a key step, where the form data is converted to fragments 
# in the CQP query language. The fragments are then put in the hashes for 
# corpora, aligned_corpora or aligned_corpora_opt

foreach my $row (@$phrases) {

    # get the name of the *first* corpus, this is defined as the "base corpus" 
    my $corpus = $in{'phrase'}->{$row}->{'corpus'}->[0];
#    print "<script>alert('$corpus')</script>";
    if ($row == 0) {
	$base_corpus=$corpus;
    }

    # for storing the cqp expression for the entire row (FIXME: aka. "phrase)
    my $cqp_query_row;

    # loop through each token in the row
    my $i=1;
    while (my $token=$in{'token'}->{$row}->{$i}) {

	# for storing the cqp expression for the token
	my $cqp_query;



	my $string_neg;                             # is it negated?
	my $string_class="word";                    # the default; can be changed to "lemma"
	my $string_case = " \%c";                   # the default: case insensitive
	my $string_string=$token->{'string'}->[0];  # the word sting

	if ($conf{'charsetfrom'}) {
#	    $string_string = $iconvr->convert($string_string);
	    Encode::from_to($string_string, $conf{'charset'}, $conf{'charsetfrom'});
	} 

	# escape special character unless the user wants to use
       # regular expressions
	unless ($in{'query'}->{'regex'}) {
	    $string_string =~ s/([\.|\?|\+|\*|\|\'|\"])/\\$1/g;
	}

	
	my $occurrence_restr;                       # store occurrence restrictions

	# loop through token attributes (POS, case etc.)
	my %atts;	
	my $atts = $token->{'atts'};
	foreach my $att (@$atts) {
	    my ($cat,$val)=split(/_/, $att);

	    # FIXME: a hack, since "_" was stupidly chosen as a delimiter 
	    $cat =~ s/~/_/g;
	    $val =~ s/~/_/g;

	    $val =~ s/ /_/g; # for multi-word-expressions

	    if ($conf{'charsetfrom'}) {
#		$val = $iconvr->convert($val);
		Encode::from_to($val, $conf{'charset'}, $conf{'charsetfrom'});
	    } 

	    # the attributes in the "word" submenu
	    if ($cat eq 'w') {
		if ($val eq 'lemma') {
		    $string_class = "lemma";
		}
		if ($val eq 'phon') {
		    $string_class = "phon";
		}
                elsif ($val eq 'orig') {
                    $string_class = "orig";
                }
		elsif ($val eq 'end') {
		    $string_string = ".*" . $string_string;
		}
		elsif ($val eq 'start') {
		    $string_string = $string_string . ".*";
		}
		elsif ($val eq 'middle') {
		    $string_string = ".+" . $string_string . ".+";
		}
		elsif ($val eq 'case') {
		    $string_case = "";
		}
		elsif ($val eq 'neg') {
		    $string_neg = 1;
		}
	    }
	    # the attributes in the "occurence" submenu
	    elsif ($cat eq 'occ') {
		$occurrence_restr=$val;
	    }
	    elsif ($val =~ s/^!//) { 	    # if the feature is negated
		$atts{'neg'}->{$cat} .= "|" . $cat . "=\"" . $val. "\"";
	    }
	    else {                              # if it's *not* negated
		# normal treatment to all others:
		$atts{'pos'}->{$cat} .= "|" . $cat . "=\"" . $val . "\"";
	    }

	}



	my @pos;  # list of non-negated cqp fragments
	my @neg;  # list of negated cqp fragments

	
	unless ($string_string eq '') {
	    if ($string_neg) {
		$atts{'neg'}->{$string_class} .= "|" . $string_class . "=\"" . $string_string . "\"" . $string_case;
	    }
	    else {
		$atts{'pos'}->{$string_class} .= "|" . $string_class . "=\"" . $string_string . "\"" . $string_case;
	    }
	}

	# start of the cqp fragment for the entire token
	$cqp_query .= "[";

	# loop through the non-negated attributes, put them in the proper list 
	my $pos = $atts{'pos'};
	if ($pos) {
	    my %pos = %$pos;
	    while (my ($cat,$vals) = each %pos) {
		my @vals = split(/\|/, $vals);
		shift @vals;
		# [AN 13.11.12]: Fjernet whitespace rundt pipe-symbolet
		my $pos = "(" . join("|", @vals) . ")";
		push @pos, $pos;
	    }
	}

	# concatenate the list of non-negated fragments to the token fragment
	if (@pos > 0) {
	   $cqp_query .= "(" . join(" & ", @pos) . ")";
	}

	# loop through the negated attributes, put them in the proper list 
	my $neg = $atts{'neg'};
	if ($neg) {
	    my %neg = %$neg;
	    while (my ($cat,$vals) = each %neg) {
		my @vals = split(/\|/, $vals);
		shift @vals;
		my $neg = "(" . join(" | ", @vals) . ")";
		push @neg, $neg;
	    }
	}

	# concatenate the list of negated fragments to the token fragment
	if (@neg > 0) {

	    # the negative fragments must be prefixed by an "&" if there are
	    # any positive ones
	    if (@pos > 0) {
		$cqp_query .= " & ";
	    }

	    $cqp_query .= " !(" . join(" | ", @neg) . ")";
	}

	# end of the cqp fragment for the entire token
	$cqp_query .= "]";

	push @token_freq, Glossa::get_token_freq($cqp_query,\%conf,$CORPUS);
	

	# add occurence restrictions
	$cqp_query .= $occurrence_restr;

       # for each token, there follows an "interval"
	# (i.e. how many unspecified tokens may follow)
	my $min = $token->{'intmin'}->[0];
	my $max = $token->{'intmax'}->[0];

	if ($min or $max) { 
	    unless ($min) { $min = 0 }  # the default is 0
	    # create cqp fragment and add to cqp expression for the token
	    $cqp_query = " []{" . $min . "," . $max . "} " . $cqp_query; 
	}
	
	# add expression for the token to expression for the row
	$cqp_query_row .= $cqp_query;
	
	$i++; # next token
	
    }
    
    
    # if fullQuery is used the previous step is not relevant:
    if ($in{'fullQuery'}) {
	$cqp_query_row = $in{'fullQuery'}->{$row}->{'string'}->[0];
    }
	
	
    # if the row is associated with the base corpus, put it in the %corpora
    # hash
    if ($corpus eq $base_corpus) {
	$corpora{$corpus}->{$cqp_query_row}=1;
    }
    # else, put it in either the %aligned_corpora or the %aligned_corpora_opt hash
    else {

	# all aligned cqp expressions are paranthesised
	$cqp_query_row = " (" . $cqp_query_row;

	# check for negation
	if ($in{'phrase'}->{$row}->{'mode'}->[0] eq 'exclude') {
	    $cqp_query_row = " !" . $cqp_query_row;
	}

	# check for optionality
	my $optalign = $in{'phrase'}->{$row}->{'optalign'}->[0]; # optionality of the row
	if ($optalign eq 'on') {
		$aligned_corpora_opt{$corpus}=1; # we only add the name of the corpus,
                                                 # since restriction does not make
		                                 # sense for optional alignment
	}
	else {
	      
	    # Non-optional alignments can be connected with either AND or OR.
            # Therefore, this section is sligthly more complex than the other ones
	    
	    # get previous expressions for rows with the same corpus name
	    my $previous_hash = $aligned_corpora{$corpus};
	    my $previous = (keys %$previous_hash)[0];
	    
	    # check the connection type (AND or OR)
	    my $connect_bool = $in{'phrase'}->{$row}->{'connectBool'}->[0];

	    if (($connect_bool eq 'and') and $previous) { 
		# non-default: join explicitly and previous delete
		my $cqp_query_both = $previous . ") :" . $corpus . " " . $cqp_query_row;
		$aligned_corpora{$corpus}->{$cqp_query_both}=1;
		delete $aligned_corpora{$corpus}->{$previous};
	    }
	    else { # use the default connection
		$aligned_corpora{$corpus}->{$cqp_query_row}=1;
	    }
	    $aligned=1; # only the non-optinal alignment sets this, since
                        # the purpose is to do optimalizations based on
                        # the viability of early query restrictions
	}
    }
    

}


# the full cqp expression for the base corpus
my $base_queries = $corpora{$base_corpus};

# stop if the query is empty
if ($$base_queries{'[]'}) {
    die("Empty queries are not allowed.\n");
}


# start the full cqp expression ($cqp_all), by
# joining rows pertaining to the base corpus
# (note: a cqp limitation forces this to always be 
# joined by "OR" (i.e. "|"); in the future AND queries
# should perhaps be hacked together by subqueries). 
my $cqp_all = "(" . join(") | (", (keys %$base_queries)) . ") ";


# add cqp expressions for aligned corpora
while (my ($k,$v) = each %aligned_corpora) {
    $cqp_all .= ":" . $k . "" . join(") | (", (keys %$v)) . ") "
}

# end it
    $cqp_all .= ";";


if ($debug) {
    print "CQP: ", $cqp_all, "<br>";
    print "base_corpus: " . $base_corpus . "<br>";
}



##                                        ##
##             2. Build subcorpus         ##
##                                        ##

# Query the database for 
# - $subcorpus: boolean, whether there are subcorpus restrictions
# - $sql_query_nl: a natural language expression for the subcorpus restrictions
# - $list: a list of allowed text-ids
# The subcorpus information (allowed token spans) is stored by the module in a .dump file
# with the rest of the files pertaining to the query.
#print LOG "PRINTER CONF\n";
#print LOG Dumper(%conf);
#print LOG "LUKKER QUERY\n";
#close(LOG);
my ($subcorpus,$sql_query_nl,$list) = Glossa::create_tid_list(\%conf, \%in, $CORPUS, \%aligned_corpora, \%aligned_corpora_opt, $base_corpus);

my %list = %$list;


my %video_stars;

if ($speech_corpus){

#while(my ($key, $val) = each %list){

    my $sth = $dbh->prepare( "SELECT tid FROM " . uc ( $CORPUS ) . "author where video = 'Y';");

    $sth->execute  ||  print TEMP "Error fetching data: $DBI::errstr";

#    print "<script> alert(\"SELECT tid FROM " . uc ( $CORPUS ) . "author where video = 'Y';\"); </script>";

    my $bzz = "";
    while (my ($v) = $sth->fetchrow_array) {
	
	$bzz .= $v . " ";
	$video_stars{ucfirst $v} = 1;
	
    }
#    print "<script>alert(' ". $bzz  ."')</script>";
#}

}
#close TEMP;

my @infs = keys %list;
my $infs = @infs;

# print natural language version
if ($sql_query_nl) {
    print "<i> $lang{'metaquery'}: $sql_query_nl</i><br />";
}

#if($CORPUS eq "nota" or $CORPUS eq "upus" or ($CORPUS eq 'scandiasyn') or $CORPUS eq 'upus2' or ($CORPUS eq 'demo')){
if($speech_corpus){
    if(!$infs){
	print "<b>The $CORPUS corpus has no informants that satisfy your search criteria.</b><br />";
	exit;
    }
    print "Informants: $infs<br />$CORPUS:<br />\n";
    foreach my $key (keys %$list){
	if($key !~ /[0-9]{3}/){
	    $list->{$key} = 0;
	}
    }
}


##                                        ##
##             3. Execute query           ##
##                                        ##



# print search expression
my $cqp_query_source2print = $cqp_all;
if ($conf{'charsetfrom'}) {
#    $cqp_query_source2print = $iconv->convert($cqp_query_source2print);
    Encode::from_to($cqp_query_source2print, $conf{'charsetfrom'}, $conf{'charset'});
} 
$cqp_query_source2print =~ s/</\&lt;/g;
$cqp_query_source2print =~ s/>/\&gt;/g;
my $top_text = "$lang{'query_string'}: <b>\"$cqp_query_source2print\"</b><br>";



# start waiting ticker
print "<div id='waiting'>searching </div>";
#print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/wait.js\"></script>\n";
#print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/", $CORPUS, ".conf.js\"></script>\n";


# initialize CWB
$WebCqp::Query::Registry = $conf{'cwb_registry'};

# get some CWB parameters
my $results_max=$in{'query'}->{'results'}->{'max'}->[0];
my $randomize=$in{'query'}->{'results'}->{'random'}->[0];
my $fastcut=$in{'query'}->{'results'}->{'fastcut'}->[0];

# initialize CWB query object
my $query = new WebCqp::Query "$base_corpus";

# print errors
$query->on_error(sub{grep {print "<h2>$_</h2>\n"} @_}); # this error needs to be dealt with in a more informative way

if($debug) {
	print Dumper %aligned_corpora;
	print Dumper %aligned_corpora_opt;
}

# specify aligned corpora
$query->alignments(keys %aligned_corpora, keys %aligned_corpora_opt); 

# get structural attributes
my $sts = $conf{'corpus_structures'}; #eg sync_time sync_end turn_endtime turn_starttime turn_speaker who_nb who_name who_line_key episode_circumstance...
my @sts = split(/ +/, $sts);

$query->structures(@sts);  # specify str-attrib. to print

# get positional attributes
my $atts = $conf{'corpus_attributes'};
my @atts = split(/ +/, $atts);

$query->attributes(@atts); # specify pos-attrib. to print
shift @atts; # it is used later, without "word" attribute (always first)


# There are three ways of reducing the number of hits. We use the 
# standard "cut" and "reduce" cqp functions (first hits or random hits) 
# if there are no restrictions due to alignment). Because of the  "cut 
# applies too early"-bug in CWB, however, the patched version of 
# the perl cqp interface has a "cut2" function that is used instead.
# (Note: cut2 is slightly slower than "cut" but insanly faster than 
# importing all hits into perl, and then cutting the array size). 
if ($randomize and $results_max) {
    $query->reduce($results_max);
}
elsif ($results_max and !$aligned and !$randomize and $fastcut) { 
    $query->cut($results_max);
}
elsif ($results_max) { 
    $query->cut2($results_max);
}

# specify name of context ("s" is default)
# FIXME: should be in config file
my $sentence_context;

#if (($CORPUS eq 'nota') or ($CORPUS eq 'demo') or ($CORPUS eq 'upus') or ($CORPUS eq 'taus') or ($CORPUS eq 'scandiasyn') or ($CORPUS eq 'upus2')) {
if($speech_corpus){
    $sentence_context='who';
}
else {
    $sentence_context='s';
}



if ($debug) {
    print "7";
}

## specify context size

# get type and size from user 
my $context_type= $in{'query'}->{'context'}->{'type'}->[0];
my $context_left= $in{'query'}->{'context'}->{'left'}->[0];
my $context_right=$in{'query'}->{'context'}->{'right'}->[0];


# one sentence is default
if ($context_type eq "chars") {                   # FIXME: should be 'words'
    $context_left = $context_left . " word";
    $context_right = $context_right . " word";
    $query->context($context_left, $context_right);
}
elsif ($context_type eq "sentences") { 
    $context_left++; $context_right++;
    $context_left = $context_left . " " . $sentence_context;
    $context_right = $context_right . " " . $sentence_context;
    $query->context($context_left, $context_right);
}
else { $query->context('1 s', '1 s'); }

# execute cqp command to restrict to subcorpus
if ($subcorpus) {
    my $dumpfile = $conf{'tmp_dir'} . "" . $conf{'query_id'} . ".dump";
    #print "DUMPFILE: $dumpfile<br>";

    $query->exec("undump QUERY < \"$dumpfile\";");
    $query->exec("QUERY;");
}


# the search-within-search feature. CQPs 'undump' function is used
# to create a subcorpus, based on the previous search (defined by a
# file created by the 'dump' function.
if (CGI::param('searchWithin') eq 'last') {
    my $dumpfile = $conf{'hits_files'} . "/" . $user . ".lastsearch";
    print "<font color=red>undump QUERY with target keyword < \"$dumpfile\";</font>";
    $query->exec("undump QUERY with target keyword < \"$dumpfile\";");
    $query->exec("QUERY;");
}

if ($debug) {
    print "8";
    print "<pre>";
    print Dumper $query;
    print "</pre>";
}

# $debug = 0;

if($debug) {
	print "8.5<br>";
	print "CQP_ALL: " . $cqp_all . "<br>";
}

# finally, execute the query
my ($result,$size) = $query->query("$cqp_all");    

if($debug) {
	print "8.6<br>";
	print "Result size: " . $size . "<br>"
}

my @result;
if ($result) {
    @result= @$result;
} 


else {
#    $cqp_query_source2print =~ /\(([\w]+)\=/;
    #([((word="koo" %c) & (pos="adj"))])
    my $str;

    while ( $cqp_query_source2print =~ s/\(([\w]+)\=//  ){

	next unless $1 !~ /word/;
	$str .= $1 . ", ";

    }
    $str =~ s/, $//; 
    my $more = "";

    if($str){ $more = $lang{'missing_tag'} . " " . $str . "."; }

    print "<b> $lang{'zero_hits'} $more</b><br><br>";

}




if (@token_freq > 1) {
    print @token_freq;
    print "<br>";
}



if ($debug) {
    print "9";
}

    
# count number of hits
my $nr_result = @result;
#my $nr_result = $size;


##                                        ##
##             4. Print result            ##
##                                        ##

# For storing all uniqe tag combinations. Will later be used to 
# create "divs" that floats over words, displaying grammatical information. 
my %tags;
my $tag_i;

# The first data file. The DATA filehandle will later be replaced, if there
# are a sufficient number of hits.
my $filename=$conf{'tmp_dir'} . "/" . $conf{'query_id'} . "_1.dat"; 
open (DATA, ">$filename");

# A file for storing a html snippet about the search (search string, links to results
# pages etc.)
my $top=$conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".top";
open (TOP, ">$top");

# Some meta-information, used by other scripts.
my $conf=$conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".conf"; 
open (CONF, ">>$conf");
print CONF "context_type=$context_type\n";
close CONF;


## links to subsidiary scripts

# The basic part of each URL
#NAME HERE?
my $actionurl = 
  "corpus=" . $in{'query'}->{'corpus'}->[0] 
  . "&query_id=" . $conf{'query_id'}
  . "&base_corpus=" . $in{'phrase'}->{0}->{'corpus'}->[0] . "&player=" . $player;
  ;

# Create a select widget. The onchange event redirects to the selected url. (The onclick event sets 
# the selected value to 0, ensuring that even when selecting the same action twice 
# the "onchange" event will still fire.) 
$top_text .= " $lang{'action'} : <select id='actionselect' onClick=\"this.options.selectedIndex=0\" onChange=\"window.location.href=(this.options[this.selectedIndex].value)\">\n<option></option>";
$top_text .= "<option value='" . $conf{'cgiRoot'} . "/count_choose.cgi?$actionurl'>$lang{'count'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} . "/download_choose.cgi?$actionurl'>$lang{'download'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} . "/sort_choose.cgi?$actionurl'>$lang{'sort'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} . "/coll_choose.cgi?$actionurl'>$lang{'collocations'}</option>\n";
                                                                                               
# only relevant for multilingual corpora
if ($conf{'type'} eq 'multilingual') {
    $top_text .= "<option value='" . $conf{'cgiRoot'} . "/cooc_choose.cgi?$actionurl'>$lang{'co-occurence'}</option> ";
}


$top_text .= "<option value='" . $conf{'cgiRoot'} . "/annotate_choose.cgi?$actionurl&atttype=$atttype'>$lang{'annotate'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} . "/meta.cgi?$actionurl'>$lang{'metadata'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} . "/meta-dist.cgi?$actionurl'>$lang{'meta-dist'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} . "/show_page_dev.cgi?$actionurl&n=1&del=yes'>$lang{'delete'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} . "/save_hits_choose.cgi?$actionurl'>$lang{'save_hits'}</option>\n";

#my $all_informants = join(",", keys %$list); #for showing all informants on map.

#$source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"window.open('$conf{'htmlRoot'}/html/profile.php?tid=$identifier&corpus=$CORPUS',");
#$source_line.=sprintf("'mywindow','height=480,width=600,status,scrollbars,resizable');\"><img src='$conf{'htmlRoot'}/html/img/i.gif' alt='i' / border='0'></a> \n&nbsp;</font>\n");


#$top_text .= "<option value='" . $conf{'htmlRoot'} . "/html/profile.php?informants=$all_informants'>show on map</option>\n";
$top_text .="</select>\n";

if($CORPUS eq 'scandiasyn' || $CORPUS eq 'amerikanorsk'){
    $top_text .= "<input type='button' onclick=\"mapper();\" value='Map' />";
    $top_text .= "<div style='float: right; top:0px;'><span onclick=\"mapper2();\">ø</span></div>";
}
$top_text .= "<br />\n";
$top_text .= "\n\n\n<!-- $top  -->\n\n\n";

#print "<script>alert('$top');</script>";

# The top text is now finished; print it to STDOUT and to file.

print TOP $top_text;
print $top_text;

# this span will later be used to hold the links to the results pages.
# (We do not yet know how many there will be. We cannot use the number of
# results, since some results may be discarded.
# FIXME: is this still true?
# )
print "<span id=\"placeholder\"></span>\n";


my $results_page = $in{'query'}->{'results'}->{'page'}->[0];
my $link_structure = $conf{'link_structure'};
my $hits;

my $c; my $d_files=1;

print "<table border=\"0\">";




my $source_line;
my $target_line;
my $alignmentp;
my $aligns=0;


# stop waiting ticker
print "<script language=\"JavaScript\">stopWait()</script>\n";


# loop through result set
my $allinfs = {};

for (my $i = 0; $i < $nr_result; $i++) {





    ##########################################
    #
    # 4.1: Structural annotation
    #
    ##########################################

    
    $source_line="";
    $target_line="";
    $alignmentp=0;

    my $m;
    # if $results_max they are already randomized
    if (($randomize) and !($results_max)) { $m = splice (@result, rand @result, 1) }
    else { $m = $result[$i] }
    #print LOG $m->{'kwic'}->{'match'} . "\n";



    # For structural annotations.
    my %sts;

    # Loop through the annotations specified in the configuration file,
    # make some corpus-specific changes, and add them to a hash.
    foreach my $a (@sts) { # @sts is array of corpus structure as defined in cgi.conf [sync_time, sync_end, turn_endtime, ...]

	# temporary fix for OMC ...
	next if (($CORPUS eq 'omc') and ($a eq 'text_id'));
	next if (($CORPUS eq 'omc4') and ($a eq 'text_id'));
	next if (($CORPUS eq 'upus') and ($a eq 'text_id'));
	next if (($CORPUS eq 'upus') and ($a eq 's_id'));
	next if (($CORPUS eq 'upus2') and ($a eq 'text_id'));
	next if (($CORPUS eq 'upus2') and ($a eq 's_id'));

	# the right way ...
	$sts{$a} = $m->{'data'}->{$a};

	$sts{$a} = $m->{'data'}->{$a};
	# temporary fix for OMC ...
	if (($CORPUS eq 'omc' or $CORPUS eq 'omc4') and ($a eq 's_id')) {
	    my $tmp = $m->{'data'}->{$a};
	    if ($tmp =~ m/([^\.]+)\.(.*)/) {
		$sts{'text_id'} = $1;
	    }
	}

	# temporary fix for NOTA
	if ($speech_corpus and ($a eq 'who_name')) {
	    $sts{'text_id'} = $m->{'data'}->{$a};
	    my $hit = $m->{'kwic'}->{'match'};
	    my $informant = $m->{'data'}->{$a};
#	    $hit =~ s/\/.*//;
	    #select only desired token for map
	    $hit =~ /[^\/]+\/[^\/]+\/([^\/]+)\//;
	    $hit = $1;
	    
	    if(!$allinfs ->{ $informant }){
		$allinfs -> { $informant } = {};
	    }
#    push(@{$self->{CHILDREN}}, $child);
	    $allinfs -> { $informant } -> { $hit }++; # 
#	    $allinfs{ $m->{'data'}->{$a} } = $allinfs{$informant}{$hit} = 1; # 
#	    $allinfs{ $m->{'data'}->{$a} } = $hit; # 
	}
	if ($speech_corpus and ($a eq 'who_line_key')) {
	    $sts{'s_id'} = $m->{'data'}->{$a};
	}
    }

    #corpus position
    $sts{'cpos'}=$m->{'cpos'};

    # get value to display from database
    if ($display_struct and !($sts{$display_struct})) {     # i.e. if the value to be displayed is not
                                                            # a cqp structural annotation
	$sts{$display_struct} = Glossa::get_metadata_feat($display_struct, $sts{'text_id'},\%conf);

    } 
    

    # structural annotations as a string (to be used later).
    my @sts_strings;
    while (my ($key, $val) = each %sts) {
	push @sts_strings, $key . "=" . $val;
    }

    my $sts_string = join("||", @sts_strings);



    ##########################################
    #
    # 4.2: Base concordance. part 11.
    #
    ##########################################

    # get the matching phrase from cqp
    my $ord = $m->{'kwic'}->{'match'};

    # get the right and left context from cqp
    my $res_r = $m->{'kwic'}->{'right'};
    my $res_l = $m->{'kwic'}->{'left'};


		# switching left and right context for right-to-left language corpora
		# but only when querying with limited word context
		# if ((($CORPUS eq 'quran_mono') or ($base_corpus eq 'UNCORPORA_AR')) and ($sentence_context eq "chars")) {
		if (($CORPUS eq 'quran_mono') or ($base_corpus eq 'UNCORPORA_AR')) {
				my $r = $res_r;
				$res_r = $res_l;
				$res_l = $r
		}
		
    # FIXME: is this still necessary?
    next if ($results_max and ($hits >= $results_max));
    $hits++;


    # Keep track of number of results in this page/datafile.
    # Change page/datafile if necessary.
    $c++;
    if ($c == $results_page) {
	$d_files++;
	close DATA;
	my $filename=$conf{'tmp_dir'} . "/" . $conf{'query_id'} . "_" . $d_files . ".dat";
	open (DATA, ">$filename");
	$c=0;
    }

    # convert the charset of the matches and context
    if ($conf{'charsetfrom'}) {
	foreach my $textstring ($res_l,$ord,$res_r) {
#	    $textstring = $iconv->convert($textstring);
	    Encode::from_to($textstring, $conf{'charsetfrom'}, $conf{'charset'});
	}
    } 

    # print to the data file
    print DATA $base_corpus, "\t", $sts{'s_id'}, "\t", $sts_string, "\t$res_l\t$ord\t$res_r\n";


    ##########################################
    #
    # 4.3. Alignment
    #
    ##########################################


    # Loop through the possible target corpora, retrieve alignement (if any).
    foreach my $a (keys %aligned_corpora, keys %aligned_corpora_opt) { 

	# Name always lowercased for CQP
	my $a = lc($a);

	# Get aligned region
	my $al = $m->{$a};
	next if ($al =~ m/^\(no alignment/);

	# Convert charset of aligned region.
	# FIXME: charset should possibly be specified by corpus, not by
	# project. (But: Future versions of CQP is supposed to support 
	# unicode ...
	if ($conf{'charsetfrom'}) {
#	    $al = $iconv->convert($al);
	    Encode::from_to($al, $conf{'charsetfrom'}, $conf{'charset'});
	} 


	# Start the alignment output.
	if ($hits < $results_page) {
	    $target_line.=sprintf("<tr bgcolor=\"#ffffff\"><td>");  # Aligned regions are gray.
	}
	$target_line .= "<tr style='color:gray'><td>";


	#
	##  Retrieve the id of the aligned region, based on the id of the matched region.
	#   (Unfortunately CQP does not offer this function; thus this hack.)

	# the name of the corpus, as a basis for the language name.
	# FIXME: this is just silly.
	my $lang = $a;
	
	# FIXME: should be correct in db
	$lang =~ s/omc3_//;
	$lang =~ s/omc4_//;
	$lang =~ s/run_//;
	$lang =~ s/subtitles_//;
	# FIXME: should be general
	if ($CORPUS eq 'samno') {
	    if ($base_corpus eq 'SAMNO_SAMISK') {  $lang = "sme" }
	    if ($base_corpus eq 'SAMNO_NORSK') {  $lang = "nob" }
	}


	# The name of the MySQL table.
	my $table = $CORPUS;
	$table = uc($table) . "s_align";


	# Id's for the aligned region.
	my $target_tid; # the text id
	my @target_sids; # one or more sentence ids

	my $t2;
	my $targets;

	# Run the query.
	my $sth = $dbh->prepare(qq{ SELECT target FROM $table where source = '$sts{'s_id'}' and lang = '$lang';});
	$sth->execute  || die "Error fetching data: $DBI::errstr";
#	my $qwerty = qq{ SELECT target FROM $table where source = '$sts{'s_id'}' and lang = '$lang';};
	#Loop through the results.
	while (my ($target) = $sth->fetchrow_array) {
	    $t2 = $target;
	    $t2 =~ s/\..*//g;
		
	    #		next unless ($texts_target{$t2});
	    
	    $targets .= "$target ";

	    $target_tid = $t2;
	    push @target_sids, $target;

	    if ($hits < $results_page) {
		
		$alignmentp=1;

		# Print links for context/metadata for the aligned regions.
		# FIXME: generaliser
		$target_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"window.open('$conf{'cgiRoot'}/show_context.cgi?s_id=$target&text_id=$t2&cs=3&corpus=$in{'query'}->{'corpus'}->[0]&subcorpus=$a',");
		$target_line.=sprintf("'mywindow','height=500,width=650,status,scrollbars,resizable');\">$target</a>\n</font>\n");
		    
		    
	    }
		
	}


	# Print the aligned regions.
	if ($hits < $results_page) {

	    $target_line .= "</td><td";
	    if ($context_type eq "chars") {
		$target_line .= " colspan=3";
	    }
	    $target_line .= ">";

	    # Output of the aligned regions. handling tags etc.
	    # (does not actually print, but adds to the "$target_line" variable,
	    # which will be printed later).
	    print_tokens_target($al, $atttype), "<br>";		

	    $target_line .= "</td></tr>";
	    
	}

	my $target_sids = join(" ", @target_sids);

	# Print to data file.
	print DATA uc($a), "\t", $target_sids, "\t", $sts_string, "\t$al\n";
	
    } # end of alignment.



    ##########################################
    #
    # 4.4. Base concordance, part 2.
    #
    ##########################################

    if ($hits < $results_page) {
	my $ex_url = "?corpus=" . $in{'query'}->{'corpus'}->[0] . "&line_key=" . $sts{'who_line_key'} . "&size=1&nested=0";
	my $line_key = $sts{'who_line_key'};
	my $sts_url = "?corpus=" . $in{'query'}->{'corpus'}->[0] . "&subcorpus=" . $base_corpus;
	while (my ($k,$v)=each %sts) {
	    $sts_url .= "&" . $k . "=" . $v;
	}
	my $identifier = $sts{'s_id'};
	if($speech_corpus){$identifier = $sts{text_id}}
	$source_line=sprintf("<tr bgcolor=\"#ffffff\">\n<td colspan=\"2\" height=\"10\">\n</td>\n</tr>\n<tr>\n<td>\n<nobr>\n");
	if($speech_corpus){
	    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"window.open('$conf{'htmlRoot'}/html/profile.php?tid=$identifier&corpus=$CORPUS',");
	    $source_line.=sprintf("'mywindow','height=600,width=600,status,scrollbars,resizable');\"><img src='$conf{'htmlRoot'}/html/img/i.gif' alt='i' / border='0'></a> \n&nbsp;</font>\n");
	}
        elsif ($CORPUS eq "skriv")
        {
            $identifier = $sts{text_id};
            my $assignment_code = join("_", (split("_", $identifier))[1,2]);
            my $assignment_path = "/michalkk/skriv/oppgavetekster/${assignment_code}.pdf";

	    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"window.open('$conf{'htmlRoot'}/html/profile.php?tid=$identifier&corpus=$CORPUS',");
	    $source_line.=sprintf("'mywindow','height=600,width=600,status,scrollbars,resizable');\"><img src='$conf{'htmlRoot'}/html/img/i.gif' alt='i' border='0'></a>&nbsp;</font>");

            if (-e "/var/www/html$assignment_path") {
                $source_line.=sprintf("<a href=\"$assignment_path\" target=\"_new\"><img src=\"/michalkk/skriv/img/assignment-text.png\" height=\"14\"/></a>&nbsp;");
            }
            my $identifier_noslash = $identifier;
            $identifier_noslash =~ s,/,_,g;
            my $answer_path = "/michalkk/skriv/oppgavesvar/${identifier_noslash}.pdf";
            if (-e "/var/www/html$answer_path") {
                $source_line.=sprintf("<a href=\"$answer_path\" target=\"_new\"><img src=\"/michalkk/skriv/img/assignment-answer.png\" height=\"14\"/></a>");
            }
        }
	else
	{
	    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"window.open('$conf{'cgiRoot'}/show_context.cgi$sts_url&cs=3',");
	    $source_line.=sprintf("'mywindow','height=500,width=650,status,scrollbars,resizable');\">$identifier</a> \n&nbsp;</font>\n");
	}
	my $phpfile = 'media3';
	if($player ne 'flash'){
	    $phpfile = 'expand';
	}
#http://tekstlab.uio.no/glossa/html/expand.php?corpus=scandiasyn&line_key=1257&size=1&nested=0&video=1
	if ($speech_corpus) {
	    if($video_stars{ucfirst $identifier}){
		if($player ne 'flash'){
		    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"document.getElementById('inspector').style.display='block';");
		    $source_line.=sprintf("document.getElementById('movie_frame').src = '$conf{'htmlRoot'}html/$phpfile.php$ex_url&video=1';\">\n");
		    $source_line.=sprintf("<img style='border-style:none' src='$conf{'htmlRoot'}html/img/mov.gif'>\n</a> \n&nbsp;</font>");
		}
		else{
		    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"document.getElementById('inspector').style.display='block';");
		    $source_line.=sprintf("player = shebang('$CORPUS', '$line_key', true);\">\n");
		    $source_line.=sprintf("<img style='border-style:none' src='$conf{'htmlRoot'}html/img/mov.gif'>\n</a> \n&nbsp;</font>");
		}
	    }
	    if($player ne 'flash'){
		$source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"document.getElementById('inspector').style.display='block';");
		$source_line.=sprintf("document.getElementById('movie_frame').src = '$conf{'htmlRoot'}html/$phpfile.php$ex_url&video=0';\">\n");
		$source_line.=sprintf("<img style='border-style:none' src='$conf{'htmlRoot'}html/img/sound.gif'>\n</a> \n&nbsp;</font>");
	    }
	    else{
		    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"document.getElementById('inspector').style.display='block';");
		    $source_line.=sprintf("player = shebang('$CORPUS', '$line_key',false);\">\n");
		    $source_line.=sprintf("<img style='border-style:none' src='$conf{'htmlRoot'}html/img/sound.gif'>\n</a> \n&nbsp;</font>");
	    }
	    $source_line.="<strong>" . $sts{"text_id"} . "</strong>&nbsp;";	    
	}
	if(!($speech_corpus and ($display_struct =~ /text\.tid/))){
	    $source_line.="<i>" . $sts{$display_struct} . "</i>";
	}
	$source_line.=sprintf("</nobr>\n</td>\n<td");
	if ($context_type eq "chars") { $source_line.=sprintf(" align=\"right\""); }
	$source_line.=sprintf(">\n");

	foreach my $a ($res_l, $res_r, $ord) {
            # temporary fixes (should be cleverer in corpus) ...
            $a =~ s/'/$apostr/g; #'
             $a =~ s/\&amp;quot;/\&quot;/g;
	}

	
	$source_line .= print_tokens($res_l, $atttype);
	if ($context_type eq "chars") {
			$source_line.=sprintf("</td><td");
			if (($CORPUS eq 'quran_mono') or ($base_corpus eq 'UNCORPORA_AR')) {
					$source_line.=sprintf(" align=\"center\" ");
			}
			$source_line.=sprintf(">");
	}
	$source_line.=sprintf("<b> &nbsp;");
	$source_line .= print_tokens($ord, $atttype);
	$source_line.=sprintf(" &nbsp;</b>");
	if ($context_type eq "chars") {
			$source_line.=sprintf("</td><td");
			if (($CORPUS eq 'quran_mono') or ($base_corpus eq 'UNCORPORA_AR')) {
					$source_line.=sprintf(" align=\"left\" ");
			}
			$source_line.=sprintf(">");
	}
	$source_line .= print_tokens($res_r, $atttype);
	$source_line.=sprintf("</td></tr>");

###
	if($parallel){
            if ($CORPUS eq "skriv") {
              $source_line .= "<tr><td></td><td align=\"right\">";
            }
            else {
              $source_line .= "<tr><td></td><td>";
            }
	    $source_line .= print_tokens($res_l, 2);
	    if ($context_type eq "chars") {$source_line.=sprintf("</td><td>"); }
	    $source_line.=sprintf("<b> &nbsp;");
	    $source_line .= print_tokens($ord, 2);
	    $source_line.=sprintf(" &nbsp;</b>");
	    if ($context_type eq "chars") { $source_line.=sprintf("</td><td>"); }
	    $source_line .= print_tokens($res_r, 2);
	    $source_line.=sprintf("</td></tr>");

	    $source_line .= "<tr><td></td><td></td></tr>";
	}
###
###
	if($speech_corpus){
#	    my $translation = print_tokens($res_l, 1) . print_tokens($ord, 1) . print_tokens($res_r, 1);
	    my $orig = get_first($res_l) . "<b>" . get_first($ord) . "</b>" . get_first($res_r);
	    $orig =~ s/"/_/g;
	    $orig =~ s/\#+/&hellip;/g;
	    $source_line .= "<tr><td></td><td>";
	    $source_line .= "<div><span onclick=\"appendTranslateScript(this.parentNode, '$orig');\" style='font-size:small;cursor:pointer;'>[translate]</span></div>";
	    $source_line.=sprintf("</td></tr>");
#<img src=\"" . $conf{'htmlRoot'} . "html/img/google-g-icon-16.png\">
	    $source_line .= "<tr><td></td><td></td></tr>";
	}
###


    }


    print $source_line;
    print $target_line;
    print  DATA "\n\n";




    

    
}

print "</table>";

#my $all_informants = "";#join(",", keys %allinfs);

#my %tok_inf_map = ();

my $tok2infs_map = {};

# %allinfs is a hash of hashes informant -> hit

foreach my $key (keys %$allinfs){
    my $toks = $allinfs -> { $key };
    foreach my $tok (keys %$toks){
	if(!$tok2infs_map ->{ $tok }){
	    $tok2infs_map -> { $tok } = {};
	}
	$tok2infs_map -> { $tok } -> { $key }++;
    }
}

# not sure if i need these bits..
my $json_inf_loc = "{";

#foreach my $key (keys %$list){
#    $json_inf_loc .= $key . "->" . $list->{$key};
#}

my $inf_locs = {};
my $all_locs = {};
my $json_tok_inf = "{";

foreach my $key ( keys %$tok2infs_map ){
    $json_tok_inf .= "\"$key\":[";
    foreach my $key2 (keys %{$tok2infs_map->{$key}}){
	$json_tok_inf .= "\"$key2\",";
	if($CORPUS eq 'scandiasyn' || $CORPUS eq 'amerikanorsk'){	
	    my $sth = $dbh->prepare( "SELECT place FROM " . uc ( $CORPUS ) . "author where tid = '$key2';");
	
#	$json_inf_loc .= "\nSELECT place FROM " . uc ( $CORPUS ) . "author where tid = '$key2';\n";
	
	    $sth->execute  ||  print TEMP "Error fetching data: $DBI::errstr";
	    
	    my @place = $sth->fetchrow();

#	$json_inf_loc .= " ---> " . @place[0] . "\n";


	    my $conv = Text::Iconv->new("ISO-8859-1", "UTF-8");
	    my $plc = $conv->convert(@place[0]);
	
	    $inf_locs->{$key2} = $plc;
	    $inf_locs->{$key2} = @place[0];
	    $all_locs->{"\"" . @place[0] . "\""} = 1;
#	    $all_locs->{"\"" . $plc . "\""} = 1;
	}
    }
    $json_tok_inf =~ s/,$//;
    $json_tok_inf .= "],\n";
}
my $json_all_locs = "[" . join(", ", keys %$all_locs) . "]";
foreach my $key (keys %$inf_locs){
    $json_inf_loc .= "\n\"" . $key . "\" : \"" . $inf_locs->{$key} ."\",";
}
$json_inf_loc =~ s/,$//;
$json_inf_loc .= "\n}";
$json_tok_inf =~ s/,$//;
$json_tok_inf .= "}";

# END OF: not sure if i need this bit..


foreach my $key (keys %$tok2infs_map){
    my $tok_hash = $tok2infs_map -> { $key };
    $tok2infs_map -> { $key } = "(" . join(",",keys %$tok_hash) . ")";
}
=start
foreach my $key (keys %$allinfs){

#    $all_informants .= $key . "(" . $allinfs{$key} . "),";
#    $tok_inf_map{$allinfs{$key}} .= $key . ",";
    my $toks = $allinfs -> { $key };
#    print "$key -> " . (join ",", keys %$toks) . "<br />";
    $tok_inf_map{$allinfs -> { $key }} = join ",", keys %$toks;
    
}
#$all_informants =~ s/,$//;
my $tok_inf_string;

foreach my $key (keys %tok_inf_map){
#    my $converter = Text::Iconv->new("ISO-8859-1", "UTF-8");
#    my $tok = $converter->convert($key);
    my $tok = $key;
    my $infs = $tok_inf_map{$key};
    $infs =~ s/,$//;
    $tok_inf_string .= $tok . "(" . $infs . "),";
}
$tok_inf_string =~ s/,$//;
=cut

=start
my $tok_inf_string;
foreach my $key (keys %$tok2infs_map){
    $tok_inf_string .= $key . $tok2infs_map -> {$key} . ",";
}
$tok_inf_string =~ s/,$//;

my $n = int(rand(9999999));
my $tok_inf_file = "/hf/foni/tekstlab/tmp/glossa/tok_inf".$n.".tmp";
open TOK_INF, ">$tok_inf_file" or die "can't open $tok_inf_file";
print TOK_INF $tok_inf_string . "\n";
close TOK_INF;
my $tok_inf_file_index = $n;
=cut

#added 20120920. Need parameters for centering the map. The are used by gmap.html (documents.opener.blablabla)
my $lat = "64";
my $lng = "3";
if($CORPUS eq 'amerikanorsk'){ $lat = "37"; $lng = "-95"; }
print "\n<script>\nvar mapObj = {\ntokInf : $json_tok_inf,\ninfLoc : $json_inf_loc,\nallLocs : $json_all_locs,\nlat : $lat,\nlng : $lng};\n</script>";
print TOP "\n<script>\nvar mapObj = {\ntokInf : $json_tok_inf,\ninfLoc : $json_inf_loc,\nallLocs : $json_all_locs,\nlat : $lat,\nlng : $lng};\n</script>";
#my $maplink = sprintf("<a href='#' onClick=\"window.open('$conf{'htmlRoot'}/html/map.php?informants=$all_informants&corpus=$CORPUS','mywindow','height=580,width=660,status,scrollbars,resizable');\"><img src='$conf{'htmlRoot'}/html/img/i.gif' alt='i' / border='0'></a>");

#my $maplink = "window.open('$conf{'htmlRoot'}/html/map.php?informants=$all_informants&corpus=$CORPUS','mywindow','height=580,width=660,status,scrollbars,resizable');";

#$maplink = "<input type='button' value='Map' onClick=\"window.open('$conf{'htmlRoot'}/html/map.php?informants=$all_informants&corpus=$CORPUS','mywindow','height=580,width=660,status,scrollbars,resizable');\" />";
#$maplink = "<a href='' window.open('$conf{'htmlRoot'}/html/map.php?informants=$all_informants&corpus=$CORPUS','mywindow','height=580,width=660,status,scrollbars,resizable');\" />";
#    my $ord = $m->{'kwic'}->{'match'};
#print "\n<script language='javascript'>\nfunction mapper(){\nwindow.open('$conf{'htmlRoot'}/html/map_hits_dev.php?informants=$tok_inf_file_index&corpus=$CORPUS','mywindow','height=780,width=1200,status,scrollbars,resizable');\n}\n</script>";
print "\n<script language='javascript'>\nfunction mapper(){\nwindow.open('$conf{'htmlRoot'}/html/gmap.html','mywindow2','height=780,width=1200,status,scrollbars,resizable');\n}\n</script>";
print TOP "\n<script language='javascript'>\nfunction mapper(){\nwindow.open('$conf{'htmlRoot'}/html/gmap.html','mywindow2','height=780,width=1200,status,scrollbars,resizable');\n}\n</script>";
#print "\n<script language='javascript'>\ndocument.getElementById('maplink').innerHTML=$maplink;\n</script>\n";

#<a href='#' ><img src='$conf{'htmlRoot'}/html/img/i.gif' alt='i' / border='0'></a>
#onClick=\"window.open('$conf{'htmlRoot'}/html/map.php?informants=$all_informants&corpus=$CORPUS','mywindow','height=580,width=660,status,scrollbars,resizable');\"
#window.open('$conf{'htmlRoot'}/html/map.php?informants=$all_informants&corpus=$CORPUS','mywindow','height=580,width=660,status,scrollbars,resizable');

    ##########################################
    #
    # 5. Cleanup.
    #
    ##########################################


## to allow tags to be show at the bottom of the page
print "<br><br><br><br><br><br><br><br><br>";

# For each unique tag, create a div that can be "floated" 
# over the appropriate tokens.
while (my ($id, $tags) = each %tags) {
    print "\n<div id=\"$id\" class=\"tag\">$tags</div>";
}


# now that we know how many results there are, print 
# links to results pages on top of page

my $max;
if ($hits == $results_max) {
    $max= " of " . $size;
}

# The javscript function (in reslist.js) to display the links to the 
# results pages (in the "placeholder" span).

#<scandiasyn>
if($parallel){$atttype = 'x'}

#</scandiasyn>
#print "<script>alert('attype: $atttype');</script>";
print "\n<script language=\"javascript\">showList($d_files,'".$conf{'query_id'}."','".$lang{'hits_found'}."',$hits,'".$lang{'results_pages'}."','$CORPUS','$max', '$atttype', '$player', '$conf{'cgiRoot'}')</script>\n";
#print "showList($d_files,'".$conf{'query_id'}."','".$lang{'hits_found'}."',$hits,'".$lang{'results_pages'}."','$CORPUS','$max', '$atttype', '$player')\n";
# print page header to file, so that it is accessible for 
# the other results pages
print TOP "$lang{'no_hits'}: <b>$hits</b> $max";
print TOP "<br>\n";
print TOP "$lang{'results_pages'}:";
foreach my $i (1..$d_files) {
    my $id = "page_" . $i;
    print TOP " <a id=\"$id\" href=\"$conf{'cgiRoot'}/show_page_dev.cgi?n=$i&query_id=$conf{'query_id'}&corpus=$CORPUS&atttype=$atttype&player=$player\">$i</a> ";
}
print "</div>";
print "</body></html>\n";



## create searchdump

# Dump the positions of the query result (start and end positions of the matching phrase 
# i.e. *not* the context.
#   This file is used for the "search-within-results" function.
#   Note that this dump is different from the subcorpus dump file.
# "cqp> undump A with target keyword < '/tmp/1179238682_77981.searchdump';"

# execute cqp command to restrict to subcorpus
my $dumpfile = $conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".searchdump";
$query->exec("dump Last > '$dumpfile';");

# add number of lines (required for cqp's 'undump' function, used for importing the dump data)
my @lines;
open (DUMP, "$dumpfile");
while (<DUMP>) {
    push @lines, $_;
}
close DUMP;
open (DUMP, ">$dumpfile");
my $len = @lines;
print DUMP $len, "\n";
print DUMP @lines;
close DUMP;

# copy to position for "last query"
my $dumpfile2 = $conf{'hits_files'} . "/" . $user . ".lastsearch";
copy($dumpfile, $dumpfile2);



#sub

sub get_first{

    my $line = shift;
    $line =~ s/\/[^ ]+//g;
    return $line;

}

sub print_tokens {
    
    my $in = shift;
    my $atts_index = shift;
    my @t = split (/ /, $in);
    my $string  ="";
    foreach my $t (@t) {

	my (@atts_token) = split(/\//, $t);
#	my $token_string = shift @atts_token;

	my $token_string = $atts_token[$atts_index];
	if($token_string eq '__UNDEF__'){ $token_string = "<span style='color: #444; font-style: italic;'>" . $atts_token[0] . "</span>"; }
	shift @atts_token;
#	$token_string = shift @atts_token;

#	$token_string = shift @atts_token;	
#	$token_string = shift @atts_token;	

	my $token_atts;

	foreach my $a (@atts) {

	    my $att_token = shift @atts_token;
	    next if ($att_token eq "_");
	    next if ($att_token eq "__UNDEF__");
	    next unless ($att_token);
	    #if ($a =~ m/_/) {
	    if ($a =~ m/_/ or $CORPUS eq 'run') {

		my $new_a = $multitags{$a}->{$att_token};
#		print $a, "::", $att_token, "->", $new_a, "<br>";
		$token_atts .= "<b>_" . $new_a . "_: </b>" . $att_token . "<br>";		
	    }
	    else {
		$token_atts .= "<b>" . $a . ": </b>" . $att_token . "<br>";		
	    }

	}

	$tag_i++;
	$string .= sprintf("<span onMouseOver=\"showTag(arguments[0], \'$tag_i\')\" onMouseOut=\"hideTag(\'$tag_i\')\">\n");
	$string .= sprintf("%s </span>",$token_string); 
	$tags{$tag_i}=$token_atts;
	## pling pling
#	print TEMP "token_atts: $token_atts\n"
    }
    return $string;
    
}
#close TEMP;
sub print_tokens_target {

    my $in = shift;
    my @t = split (/ /, $in);

    foreach my $t (@t) {

	my (@atts_token) = split(/\//, $t);
	my $token_string = shift @atts_token;

	my $token_atts;

	foreach my $a (@atts) {
	    my $att_token = shift @atts_token;
	    next if ($att_token eq "_");
	    next if ($att_token eq "__UNDEF__");
	    next unless ($att_token);
	    #if ($a =~ m/_/) {
	    if ($a =~ m/_/ or $CORPUS eq 'run') {

		my $new_a = $multitags{$a}->{$att_token};

		$token_atts .= "<b>" . $new_a . ": </b>" . $att_token . "<br>";		
	    }
	    else {
		$token_atts .= "<b>" . $a . ": </b>" . $att_token . "<br>";		
	    }
	}

	$tag_i++;
	$target_line.=sprintf("<span onMouseOver=\"showTag(arguments[0], \'$tag_i\')\" onMouseOut=\"hideTag(\'$tag_i\')\">\n");
	$target_line.=sprintf("%s </span>",$token_string); 
	$tags{$tag_i}=$token_atts;

    }
}
