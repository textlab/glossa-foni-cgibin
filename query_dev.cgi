#!/usr/bin/perl

use CGI::Carp qw(fatalsToBrowser);
use strict;
use CGI qw/:standard/;
use POSIX;
use Data::Dumper;
use DBI;
use WebCqp::Query_dev; # this is the modified version of the module
use File::Copy;
use Text::Iconv;
use Encode;

# Use Glossa module embedded in repo
use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

##                                        ##
##             0. Initialization          ##
##                                        ##

my $logger = Glossa::getLogger('query_dev');

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

my $atttype = $cgi->param('atttype');

#<scandiasyn>

my $parallel = 0;
if($atttype eq 'x'){$parallel = 2; $atttype = 0}
#</scandiasyn>

my %in = Glossa::create_params();

my $CORPUS = $in{'query'}->{'corpus'}->[0];
$logger->info("Corpus id $CORPUS");

my $user = $ENV{'REMOTE_USER'};
my $display_struct = CGI::param('structDisplay');
my $player = CGI::param('player');

my %conf = GlossaConfig::readConfig($CORPUS);

my $corpus_mode = $conf{'corpus_mode'};

$logger->info("Corpus mode is $corpus_mode");

my $speech_corpus = 0;

if($corpus_mode eq 'speech') {
    $logger->info("Corpus is a speech corpus");
    $speech_corpus = 1;
}

# multitag file
my %multitags = GlossaConfig::readMultitagFile(%conf);

# language file
my %lang = Glossa::readLanguageFile(%conf);


## start the HTTP session and HTML file
print header(-type=>'text/html', -charset=>$conf{'charset'});

# collect script and html tags for head section
my @header_html_elts = (Link({-rel=>'shortcut icon',
                              -href=>'favicon.ico',
                              -type=>'image/ico'}),
                        Link({-rel=>'stylesheet',
                              -href=>"$conf{'htmlRoot'}/html/tags.css",
                              -type=>'text/css'}));

my @header_script_elts = ({-type=>'text/javascript',
                           -src=>"$conf{'htmlRoot'}/js/wait.js"},
                          {-type=>'text/javascript',
                           -src=>"$conf{'htmlRoot'}/js/$CORPUS.conf.js"},
                          {-type=>'text/javascript',
                           -src=>"$conf{'htmlRoot'}/js/reslist.js"},
                          {-type=>'text/javascript',
                           -src=>"$conf{'htmlRoot'}/js/showtag.js"});

# charset is set correctly in cgi.conf for these corpora,
# shouldn't be necessary to do it here
if($CORPUS eq 'mak') {
    push(@header_html_elts, meta({(-http_equiv)=>'"Content-Type',
                                  -content=>'text/html', -charset=>'ISO-8859-5'}));
}
elsif($CORPUS eq 'latvian') {
    push(@header_html_elts, meta({(-http_equiv)=>'"Content-Type',
                                  -content=>'text/html', -charset=>'CP1257'}));

}
elsif($CORPUS eq 'run') {
    push(@header_html_elts, meta({(-http_equiv)=>'"Content-Type',
                                  -content=>'text/html', -charset=>'UTF-8'}));
}

if ($speech_corpus) {
    push(@header_html_elts, Link({-rel=>'stylesheet',
                                  -href=>"http://ajax.googleapis.com/" .
                                      "ajax/libs/jqueryui/1.8.6/themes/" .
                                      "base/jquery-ui.css",
                                  -type=>'text/css',
                                  -media=>'all'}));

    push(@header_html_elts, Link({-rel=>'stylesheet',
                                  -href=>"http://static.jquery.com/" .
                                      "ui/css/demo-docs-theme/ui.theme.css",
                                  -type=>'text/css',
                                  -media=>'all'}));

    push(@header_html_elts, Link({-rel=>'stylesheet',
                                  -href=>"$conf{'htmlRoot'}/player/player.css",
                                  -type=>'text/css'}));

    push(@header_html_elts, Link({-rel=>'stylesheet',
                                  -href=>"$conf{'htmlRoot'}/html/tags.css",
                                  -type=>'text/css'}));

    push(@header_script_elts, {-type=>'text/javascript',
                               -src=>"$conf{'htmlRoot'}/player/player.ajax.js"});
    
    push(@header_script_elts, {-type=>'text/javascript',
                               -src=>"$conf{'htmlRoot'}/js/showtag.js"});

    push(@header_script_elts, {-type=>'text/javascript',
                               -src=>"$conf{'htmlRoot'}" .
                                   "/js/jquery/jquery-1.4.3.min.js"});
    
    push(@header_script_elts, {-type=>'text/javascript',
                               -src=>$conf{'htmlRoot'} .
                                   "/js/jquery/jquery-ui-1.8.6.custom.min.js"});

    push(@header_script_elts, {-type=>'text/javascript',
                               -src=>"$conf{'htmlRoot'}/player/slider.js"});


    push(@header_script_elts, {-type=>'text/javascript',
                               -code=>"var player;"});
}

# google translate js code
push(@header_script_elts, {-type=>'text/javascript',
                           -src=>"http://www.google.com/jsapi"});
push(@header_script_elts, {-type=>'text/javascript',
                           -src=>"$conf{'htmlRoot'}/js/google_trans.js"});

push(@header_html_elts, Link({-rel=>'stylesheet',
                              -href=>"$conf{'htmlRoot'}/html/inspect.css",
                              -type=>'text/css'}));

# generate HEAD section
print start_html(-head=>\@header_html_elts,
                 -title=>$lang{'title'},
                 -script=>\@header_script_elts);

print Glossa::create_media_player_div($player, %conf);

print "  <div id=\"body\">\n";

# additional group file access
if (not Glossa::check_group_file_access($user, %conf)) {
    die("You do not have access to this corpus.");
}

## Set query id
$conf{'query_id'} = Glossa::createQueryId();

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

# "opt" = optional
my %aligned_corpora_opt;               

# name of base corpus (i.e. non-aligned)
my $base_corpus;

# boolean: indicate if there are restrictions on aligned corpora
my $aligned;

# the number of phrases (i.e. "rows" in the interface)
my $phrases=$in{'phrase'}->{'number'}; 

my @token_freq;

$logger->info("$phrases");

## Loop through all the phrases
# This is a key step, where the form data is converted to fragments 
# in the CQP query language. The fragments are then put in the hashes for 
# corpora, aligned_corpora or aligned_corpora_opt

foreach my $row (@$phrases) {
    # get the name of the *first* corpus, this is defined as the "base corpus" 
    my $corpus = $in{'phrase'}->{$row}->{'corpus'}->[0];

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

        # is it negated?
        my $string_neg;

        # the default; can be changed to "lemma"
        my $string_class="word";

        # the default: case insensitive
        my $string_case = " \%c";

        # the word sting
        my $string_string=$token->{'string'}->[0]; 

        if ($conf{'charsetfrom'}) {
            Encode::from_to($string_string, $conf{'charset'}, $conf{'charsetfrom'});
        } 

        # escape special character unless the user wants to use
        # regular expressions
        unless ($in{'query'}->{'regex'}) {
            $string_string =~ s/([\.|\?|\+|\*|\|\'|\"])/\\$1/g;
        }

        # store occurrence restrictions
        my $occurrence_restr;   

        # loop through token attributes (POS, case etc.)
        my %atts;	
        my $atts = $token->{'atts'};
        foreach my $att (@$atts) {
            my ($cat,$val)=split(/_/, $att);

            # FIXME: a hack, since "_" was stupidly chosen as a delimiter 
            $cat =~ s/~/_/g;
            $val =~ s/~/_/g;

            # for multi-word-expressions
            $val =~ s/ /_/g;    

            # to allow looking for strings containing space
            $val =~ s/@@@/ /g;

            if ($conf{'charsetfrom'}) {
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
            elsif ($val =~ s/^!//) { # if the feature is negated
                $atts{'neg'}->{$cat} .= "|" . $cat . "=\"" . $val. "\"";
            }
            elsif ($cat eq 'cmt') {
                $string_string = '\(.*' . $string_string . '.*\)';
            }
            else {              # if it's *not* negated
                # normal treatment to all others:
                $atts{'pos'}->{$cat} .= "|" . $cat . "=\"" . $val . "\"";
            }

        }

        my @pos;                # list of non-negated cqp fragments
        my @neg;                # list of negated cqp fragments

        unless ($string_string eq '') {
            if ($string_neg) {
                $atts{'neg'}->{$string_class} .= "|" .
                    $string_class . "=\"" . $string_string . "\"" . $string_case;
            }
            else {
                $atts{'pos'}->{$string_class} .= "|" .
                    $string_class . "=\"" . $string_string . "\"" . $string_case;
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
            unless ($min) { $min = 0 } # the default is 0
            # create cqp fragment and add to cqp expression for the token
            $cqp_query = " []{" . $min . "," . $max . "} " . $cqp_query; 
        }

        # add expression for the token to expression for the row
        $cqp_query_row .= $cqp_query;

        # next token
        $i++;                   
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

        # optionality of the row
        my $optalign = $in{'phrase'}->{$row}->{'optalign'}->[0];

        if ($optalign eq 'on') {
            # we only add the name of the corpus,
            # since restriction does not make
            # sense for optional alignment
            $aligned_corpora_opt{$corpus}=1; 
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
                my $cqp_query_both = $previous . ") :" . $corpus .
                    " " . $cqp_query_row;
                $aligned_corpora{$corpus}->{$cqp_query_both}=1;
                delete $aligned_corpora{$corpus}->{$previous};
            }
            else {              # use the default connection
                $aligned_corpora{$corpus}->{$cqp_query_row}=1;
            }

            # only the non-optinal alignment sets this, since
            # the purpose is to do optimalizations based on
            # the viability of early query restrictions
            $aligned=1;
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

##                                        ##
##             2. Build subcorpus         ##
##                                        ##

# Query the database for 
# - $subcorpus: boolean, whether there are subcorpus restrictions
# - $sql_query_nl: a natural language expression for the subcorpus restrictions
# - $list: a list of allowed text-ids
# The subcorpus information (allowed token spans) is stored by the module in a .dump file
# with the rest of the files pertaining to the query.

my ($subcorpus,$sql_query_nl,$list) =
    Glossa::create_tid_list(\%conf, \%in, $CORPUS, \%aligned_corpora,
                            \%aligned_corpora_opt, $base_corpus);

my %list = %$list;

my %video_stars;

if ($speech_corpus) {
    my $sth = $dbh->prepare( "SELECT tid FROM " . uc ( $CORPUS ) .
                             "author where video = 'Y';");

    $sth->execute  ||  print TEMP "Error fetching data: $DBI::errstr";

    my $bzz = "";

    while (my ($v) = $sth->fetchrow_array) {
        $bzz .= $v . " ";
        $video_stars{ucfirst $v} = 1;
    }
}

my @infs = keys %list;
my $infs = @infs;

# print natural language version
if ($sql_query_nl) {
    print "<i> $lang{'metaquery'}: $sql_query_nl</i><br />";
}

if ($speech_corpus) {
    print "<img src='http://tekstlab.uio.no/glossa/html/img/tri.png' alt='caution'>";
    print "<b>The videos in this corpus are currently unavailable for Internet Explorer 9 and 10. The issue is being resolved (2014.02.03)</b><br />";
    if(!$infs) {
        print "<b>The $CORPUS corpus has no informants that satisfy " .
            "your search criteria.</b><br />";
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
    Encode::from_to($cqp_query_source2print, $conf{'charsetfrom'}, $conf{'charset'});
} 

$cqp_query_source2print =~ s/</\&lt;/g;
$cqp_query_source2print =~ s/>/\&gt;/g;
my $top_text = "$lang{'query_string'}: <b>\"$cqp_query_source2print\"</b><br>";

# start waiting ticker
print "<div id='waiting'>searching </div>";

# initialize CWB
$WebCqp::Query::Registry = $conf{'cwb_registry'};

# get some CWB parameters
my $results_max=$in{'query'}->{'results'}->{'max'}->[0];
my $randomize=$in{'query'}->{'results'}->{'random'}->[0];
my $fastcut=$in{'query'}->{'results'}->{'fastcut'}->[0];

# initialize CWB query object
my $query = new WebCqp::Query "$base_corpus";

# print errors
# this error needs to be dealt with in a more informative way
$query->on_error(sub{grep {print "<h2>$_</h2>\n"} @_}); 

# specify aligned corpora
$query->alignments(keys %aligned_corpora, keys %aligned_corpora_opt); 

# get structural attributes
# eg sync_time sync_end turn_endtime turn_starttime turn_speaker
# who_nb who_name who_line_key episode_circumstance...
my $sts = $conf{'corpus_structures'}; 
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

if($speech_corpus){
    $sentence_context='who';
}
else {
    $sentence_context='s';
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

# finally, execute the query
my ($result,$size) = $query->query("$cqp_all");    

my @result;

if ($result) {
    @result= @$result;
} 
else {
    my $str;

    while ( $cqp_query_source2print =~ s/\(([\w]+)\=//  ) {
        next unless $1 !~ /word/;
        $str .= $1 . ", ";
    }

    $str =~ s/, $//; 
    my $more = "";

    if ($str) {
        $more = $lang{'missing_tag'} . " " . $str . ".";
    }

    print "<b> $lang{'zero_hits'} $more</b><br><br>";
}

if (@token_freq > 1) {
    print @token_freq;
    print "<br>";
}
    
# count number of hits
my $nr_result = @result;

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
$top_text .= " $lang{'action'} : <select id='actionselect' " .
    "onClick=\"this.options.selectedIndex=0\" ".
    "onChange=\"window.location.href=(this.options[this.selectedIndex].value)\">" .
    "\n<option></option>";
$top_text .= "<option value='" . $conf{'cgiRoot'} .
    "/count_choose.cgi?$actionurl'>$lang{'count'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} .
    "/download_choose.cgi?$actionurl'>$lang{'download'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} .
    "/sort_choose.cgi?$actionurl'>$lang{'sort'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} .
    "/coll_choose.cgi?$actionurl'>$lang{'collocations'}</option>\n";                                                                                           
# only relevant for multilingual corpora
if ($conf{'type'} eq 'multilingual') {
    $top_text .= "<option value='" . $conf{'cgiRoot'} .
        "/cooc_choose.cgi?$actionurl'>$lang{'co-occurence'}</option> ";
}

$top_text .= "<option value='" . $conf{'cgiRoot'} .
    "/annotate_choose.cgi?$actionurl&atttype=$atttype'>$lang{'annotate'}</option>\n";
if(!$speech_corpus){
    $top_text .= "<option value='" . $conf{'cgiRoot'} .
	"/meta.cgi?$actionurl'>$lang{'metadata'}</option>\n";
    $top_text .= "<option value='" . $conf{'cgiRoot'} .
	"/meta-dist.cgi?$actionurl'>$lang{'meta-dist'}</option>\n";
}
$top_text .= "<option value='" . $conf{'cgiRoot'} .
    "/show_page_dev.cgi?$actionurl&n=1&del=yes'>$lang{'delete'}</option>\n";
$top_text .= "<option value='" . $conf{'cgiRoot'} .
    "/save_hits_choose.cgi?$actionurl'>$lang{'save_hits'}</option>\n";

$top_text .="</select>\n";

# HERE! NEED TO ADD MAP ATTRIBUTE TO CONFIG!!
if($CORPUS eq 'scandiasyn' || $CORPUS eq 'amerikanorsk' || $CORPUS eq 'sls') {
    $top_text .= "<input type='button' onclick=\"mapper();\" value='Map' />";
    $top_text .= "<div style='float: right; top:0px;'>" .
        "<span onclick=\"mapper2();\">ø</span></div>\n";
}

$top_text .= "<br />\n";
$top_text .= "\n\n\n<!-- $top  -->\n\n\n";

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
    if (($randomize) and !($results_max)) {
        $m = splice (@result, rand @result, 1)
    }
    else {
        $m = $result[$i]
    }

    # For structural annotations.
    my %sts;

    # Loop through the annotations specified in the configuration file,
    # make some corpus-specific changes, and add them to a hash.

    # @sts is array of corpus structure as defined in cgi.conf
    # [sync_time, sync_end, turn_endtime, ...]
    foreach my $a (@sts) { 
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

            #select only desired token for map
            $hit =~ /[^\/]+\/[^\/]+\/([^\/]+)\//;
            $hit = $1;

            if(!$allinfs ->{ $informant }){
                $allinfs -> { $informant } = {};
            }
            $allinfs -> { $informant } -> { $hit }++;
        }
        if ($speech_corpus and ($a eq 'who_line_key')) {
            $sts{'s_id'} = $m->{'data'}->{$a};
        }
    }

    #corpus position
    $sts{'cpos'}=$m->{'cpos'};

    # get value to display from database
    # i.e. if the value to be displayed is not
    if ($display_struct and !($sts{$display_struct})) { 
        # a cqp structural annotation
        $sts{$display_struct} =
            Glossa::get_metadata_feat($display_struct, $sts{'text_id'},\%conf);
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
        my $filename=$conf{'tmp_dir'} . "/" . $conf{'query_id'} .
            "_" . $d_files . ".dat";
        open (DATA, ">$filename");
        $c=0;
    }

    # convert the charset of the matches and context
    if ($conf{'charsetfrom'}) {
        foreach my $textstring ($res_l,$ord,$res_r) {
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
            Encode::from_to($al, $conf{'charsetfrom'}, $conf{'charset'});
        } 

        # Start the alignment output.
        if ($hits < $results_page) {
            # Aligned regions are gray.
            $target_line.=sprintf("<tr bgcolor=\"#ffffff\"><td>");
        }

        $target_line .= "<tr style='color:gray'><td>";

        # Retrieve the id of the aligned region, based on the id
        # of the matched region.
        # (Unfortunately CQP does not offer this function; thus this hack.)

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
        my $target_tid;         # the text id
        my @target_sids;        # one or more sentence ids

        my $t2;
        my $targets;

        # Run the query.
        my $sth = $dbh->prepare(qq{ SELECT target FROM $table where source = '$sts{'s_id'}' and lang = '$lang';});
        $sth->execute  || die "Error fetching data: $DBI::errstr";

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
                $target_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                      "onClick=\"window.open('$conf{'cgiRoot'}" .
                                      "/show_context.cgi?s_id=$target&" .
                                      "text_id=$t2&cs=3&corpus=" .
                                      "$in{'query'}->{'corpus'}->[0]&subcorpus=$a',");
                $target_line.=sprintf("'mywindow','height=500,width=650,status," .
                                      "scrollbars,resizable');\">" .
                                      "$target</a>\n</font>\n");
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
    }

    # end of alignment.

    ##########################################
    #
    # 4.4. Base concordance, part 2.
    #
    ##########################################

    if ($hits < $results_page) {
        my $ex_url = "?corpus=" . $in{'query'}->{'corpus'}->[0] . "&line_key=" .
            $sts{'who_line_key'} . "&size=1&nested=0";
        my $line_key = $sts{'who_line_key'};
        my $sts_url = "?corpus=" . $in{'query'}->{'corpus'}->[0] . "&subcorpus=" .
            $base_corpus;

        while (my ($k,$v)=each %sts) {
            $sts_url .= "&" . $k . "=" . $v;
        }

        my $identifier = $sts{'s_id'};

        if($speech_corpus) {
            $identifier = $sts{text_id}
        }

        $source_line = sprintf("<tr bgcolor=\"#ffffff\">\n<td colspan=\"2\" " .
                               "height=\"10\">\n</td>\n</tr>\n<tr>\n<td>\n<nobr>\n");
        if ($speech_corpus) {
            $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                  "onClick=\"window.open('$conf{'htmlRoot'}" .
                                  "/html/profile.php?tid=$identifier&" .
                                  "corpus=$CORPUS',");
            $source_line.=sprintf("'mywindow','height=600,width=600,status," .
                                  "scrollbars,resizable');\">" .
                                  "<img src='$conf{'htmlRoot'}/html/img/i.gif' " .
                                  "alt='i' / border='0'></a> \n&nbsp;</font>\n");
        }
        elsif ($CORPUS eq "skriv" || $CORPUS eq "norm")
        {
            $identifier = $sts{text_id};
            my $assignment_code = join("_", (split("_", $identifier))[1,2]);
            my $assignment_path = "/skriv/oppgavetekster/${assignment_code}.pdf";

            $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                  "onClick=\"window.open('$conf{'htmlRoot'}" .
                                  "/html/profile.php?tid=$identifier&" .
                                  "corpus=$CORPUS',");
            $source_line.=sprintf("'mywindow','height=600,width=600,status," .
                                  "scrollbars,resizable');\">" .
                                  "<img border=\"0\" src='$conf{'htmlRoot'}/html/img/i.gif' " .
                                  "alt='i' border='0'></a>&nbsp;</font>");

            if (-e "/var/www/html$assignment_path") {
                $source_line.=sprintf("<a href=\"$assignment_path\" " .
                                      "target=\"_new\"><img border=\"0\" src=\"/skriv/" .
                                      "img/assignment-text.png\" height=\"14\"/>" .
                                      "</a>&nbsp;");
            }
            my $identifier_noslash = $identifier;
            $identifier_noslash =~ s,/,_,g;
            my $answer_path = "/$CORPUS/oppgavesvar/${identifier_noslash}.pdf";
            if (-e "/var/www/html$answer_path") {
                $source_line.=sprintf("<a href=\"$answer_path\" target=\"_new\">" .
                                      "<img border=\"0\" src=\"/skriv/img/" .
                                      "assignment-answer.png\" height=\"14\"/></a>");
            }
        }
        else {
            $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                  "onClick=\"window.open('$conf{'cgiRoot'}" .
                                  "/show_context.cgi$sts_url&cs=3',");
            $source_line.=sprintf("'mywindow','height=500,width=650,status," .
                                  "scrollbars,resizable');\">$identifier</a> " .
                                  "\n&nbsp;</font>\n");
        }
        
        my $phpfile = 'media3';

        if ($player ne 'flash') {
            $phpfile = 'expand';
        }

        if ($speech_corpus) {
            if($video_stars{ucfirst $identifier}){
                if($player ne 'flash'){
                    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                          "onClick=\"document.getElementById(" .
                                          "'inspector').style.display='block';");
                    $source_line.=sprintf("document.getElementById('movie_frame')" .
                                          ".src = '$conf{'htmlRoot'}/html/" .
                                          "$phpfile.php$ex_url&video=1';\">\n");
                    $source_line.=sprintf("<img style='border-style:none' " .
                                          "src='$conf{'htmlRoot'}/html/img/" .
                                          "mov.gif'>\n</a> \n&nbsp;</font>");
                }
                else{
                    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                          "onClick=\"document.getElementById(" .
                                          "'inspector').style.display='block';");
                    $source_line.=sprintf("player = shebang('$CORPUS', " .
                                          "'$line_key', true);\">\n");
                    $source_line.=sprintf("<img style='border-style:none' " .
                                          "src='$conf{'htmlRoot'}/html/img/" .
                                          "mov.gif'>\n</a> \n&nbsp;</font>");
                }
            }

            my $show_context = ($CORPUS eq "legepasient") ? "vis.jpg" : "sound.gif";
            if($player ne 'flash'){
                $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                      "onClick=\"document.getElementById(" .
                                      "'inspector').style.display='block';");
                $source_line.=sprintf("document.getElementById('movie_frame').src" .
                                      " = '$conf{'htmlRoot'}/html/" .
                                      "$phpfile.php$ex_url&video=0';\">\n");
                $source_line.=sprintf("<img style='border-style:none' " .
                                      "src='$conf{'htmlRoot'}/html/img/$show_context' width=\"17\">" .
                                      "</a> \n&nbsp;</font>");
            }
            else{
                $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                      "onClick=\"document.getElementById(" .
                                      "'inspector').style.display='block';");
                $source_line.=sprintf("player = shebang('$CORPUS', '$line_key', " .
                                      "false);\">\n");
                $source_line.=sprintf("<img style='border-style:none' " .
                                      "src='$conf{'htmlRoot'}/html/img/" .
                                      "$show_context' width=\"17\"></a> \n&nbsp;</font>");
            }
            $source_line.="<strong>" . $sts{"text_id"} . "</strong>&nbsp;";	    
        }

        if(!($speech_corpus and ($display_struct =~ /text\.tid/))) {
            $source_line.="<i>" . $sts{$display_struct} . "</i>";
        }

        $source_line.=sprintf("</nobr>\n</td>\n<td");

        if ($context_type eq "chars") {
            $source_line.=sprintf(" align=\"right\"");
        }

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

        if($parallel){
            if ($CORPUS eq "skriv" || $CORPUS eq "norm") {
                $source_line .= "<tr><td></td><td align=\"right\">";
            }
            else {
                $source_line .= "<tr><td></td><td>";
            }

            $source_line .= print_tokens($res_l, 2);

            if ($context_type eq "chars") {
                $source_line.=sprintf("</td><td>");
            }

            $source_line.=sprintf("<b> &nbsp;");
            $source_line .= print_tokens($ord, 2);
            $source_line.=sprintf(" &nbsp;</b>");

            if ($context_type eq "chars") {
                $source_line.=sprintf("</td><td>");
            }

            $source_line .= print_tokens($res_r, 2);
            $source_line.=sprintf("</td></tr>");

            $source_line .= "<tr><td></td><td></td></tr>";
        }

        if($speech_corpus){
            my $orig = get_first($res_l) . "<b>" . get_first($ord) .
                "</b>" . get_first($res_r);
            $orig =~ s/"/_/g;
            $orig =~ s/\#+/&hellip;/g;
            $source_line .= "<tr><td></td><td>";
            $source_line .= "<div><span onclick=\"appendTranslateScript(" .
                "this.parentNode, '$orig');\" style='font-size:small;cursor:" .
                "pointer;'>[translate]</span></div>";
            $source_line.=sprintf("</td></tr>");
            $source_line .= "<tr><td></td><td></td></tr>";
        }
    }

    print $source_line;
    print $target_line;
    print  DATA "\n\n";
}

print "</table>";

my $tok2infs_map = {};

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

my $inf_locs = {};
my $all_locs = {};
my $json_tok_inf = "{";

foreach my $key ( keys %$tok2infs_map ) {
    $json_tok_inf .= "\"$key\":[";
    
    foreach my $key2 (keys %{$tok2infs_map->{$key}}){
        $json_tok_inf .= "\"$key2\",";
        
        if($CORPUS eq 'scandiasyn' || $CORPUS eq 'amerikanorsk' || $CORPUS eq 'sls'){	
            my $sth = $dbh->prepare( "SELECT place FROM " . uc ( $CORPUS ) .
                                     "author where tid = '$key2';");

            $sth->execute  ||  print TEMP "Error fetching data: $DBI::errstr";

            my @place = $sth->fetchrow();

            my $conv = Text::Iconv->new("ISO-8859-1", "UTF-8");
            my $plc = $conv->convert(@place[0]);

            $inf_locs->{$key2} = $plc;
            $inf_locs->{$key2} = @place[0];
            $all_locs->{"\"" . @place[0] . "\""} = 1;
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


#added 20120920. Need parameters for centering the map. The are used by gmap.html (documents.opener.blablabla)

my $lat = $conf{'map_lat'};
my $lng = $conf{'map_lng'};


print "\n<script>\nvar mapObj = {\ntokInf : $json_tok_inf,\ninfLoc : " .
    "$json_inf_loc,\nallLocs : $json_all_locs,\nlat : $lat,\nlng : " .
    "$lng};\n</script>";
print TOP "\n<script>\nvar mapObj = {\ntokInf : $json_tok_inf,\ninfLoc : " .
    "$json_inf_loc,\nallLocs : $json_all_locs,\nlat : $lat,\nlng : $lng};\n" .
    "</script>\n";

print "\n<script language='javascript'>\nfunction mapper()" .
    "{\nwindow.open('$conf{'htmlRoot'}/html/gmap.html','mywindow2','height=780," .
    "width=1200,status,scrollbars,resizable');\n}\n</script>";
print TOP "\n<script language='javascript'>\nfunction mapper()".
    "{\nwindow.open('$conf{'htmlRoot'}/html/gmap.html','mywindow2','height=780,".
    "width=1200,status,scrollbars,resizable');\n}\n</script>\n";

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

print "\n<script language=\"javascript\">showList($d_files,'" . $conf{'query_id'} .
    "','" . $lang{'hits_found'} . "',$hits,'" . $lang{'results_pages'} .
    "','$CORPUS','$max', '$atttype', '$player', '$conf{'cgiRoot'}')</script>\n";

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

# Dump the positions of the query result (start and end positions of
# the matching phrase 
# i.e. *not* the context.
#   This file is used for the "search-within-results" function.
#   Note that this dump is different from the subcorpus dump file.
# "cqp> undump A with target keyword < '/tmp/1179238682_77981.searchdump';"

# execute cqp command to restrict to subcorpus
my $dumpfile = $conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".searchdump";
$query->exec("dump Last > '$dumpfile';");

# add number of lines (required for cqp's 'undump' function, used
# for importing the dump data)
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
        my $token_string = $atts_token[$atts_index];
        if ($CORPUS eq 'legepasient') {
          $token_string =~ y/{}/[]/;
        }

        if($token_string eq '__UNDEF__') {
            $token_string = "<span style='color: #444; font-style: italic;'>" .
                $atts_token[0] . "</span>";
        }

        shift @atts_token;

        my $token_atts;

        foreach my $a (@atts) {
            my $att_token = shift @atts_token;
            next if ($att_token eq "_");
            next if ($att_token eq "__UNDEF__");
            next unless ($att_token);

            if ($a =~ m/_/ or $CORPUS eq 'run') {
                my $new_a = $multitags{$a}->{$att_token};
                $token_atts .= "<b>_" . $new_a . "_: </b>" . $att_token . "<br>";		
            }
            else {
                $token_atts .= "<b>" . $a . ": </b>" . $att_token . "<br>";		
            }
        }

        $tag_i++;
        $string .= sprintf("<span onMouseOver=\"showTag(arguments[0], " .
                           "\'$tag_i\')\" onMouseOut=\"hideTag(\'$tag_i\')\">\n");
        $string .= sprintf("%s </span>",$token_string); 
        $tags{$tag_i}=$token_atts;
    }
    return $string;

}

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
