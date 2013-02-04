#!/usr/bin/perl

use CGI;
use DBI;
use Data::Dumper;
use lib("./lib/");
use Glossa_local;
use strict;

# variables $query_id and $corpus ends up on the command line; 
# must be checked for nastiness (like "taint")
my $query_id = CGI::param('query_id');
my $corpus=CGI::param('corpus');
my $atttype=CGI::param('atttype');
my $player = CGI::param('player');

#<scandiasyn>
my $parallel = 0;
my $atttype_copy = $atttype;
if($atttype eq 'x'){$parallel = 2; $atttype = 0;}
#</scandiasyn>

unless ($query_id =~ m/^\d+_\d+$/) { die("illegal value") };

my %in;

my $hits_name=CGI::param('name');

my $user = $ENV{'REMOTE_USER'}; 

my %conf=Glossa::readConfig($corpus);

my $corpus_mode = $conf{'corpus_mode'};

my $speech_corpus = 0;

if($corpus_mode eq 'speech'){
    $speech_corpus = 1;
}
my $video_scripts = <<STOP;

   <link rel="stylesheet"
    href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.6/themes/base/jquery-ui.css"
    type="text/css" media="all" />
   <link rel="stylesheet"
    href="http://static.jquery.com/ui/css/demo-docs-theme/ui.theme.css"
    type="text/css" media="all" />
   <link rel="stylesheet" type="text/css"
    href="$conf{'htmlRoot'}/player/player.css" />
   <link href="$conf{'htmlRoot'}/html/tags.css" rel="stylesheet" type="text/css" />
   <script type='text/javascript' src="$conf{'htmlRoot'}/player/player.ajax.js">
    </script>
   <script language="JavaScript" src="$conf{'htmlRoot'}/js/showtag.js" ></script>
   <script type='text/javascript'
    src="$conf{'htmlRoot'}/js/jquery/jquery-1.4.3.min.js"></script>
   <script type='text/javascript'
    src="$conf{'htmlRoot'}/js/jquery/jquery-ui-1.8.6.custom.min.js"></script>
   <script type='text/javascript' src="$conf{'htmlRoot'}/player/slider.js"></script>
   <script type='text/javascript'>var player;</script>

STOP
    
my $googletrans = <<STOP;

<script type="text/javascript" src="http://www.google.com/jsapi"></script>
<script type="text/javascript">

var globalNodeVar;

function appendTranslateScript(node,text){
    globalNodeVar = node;
    var newScript = document.createElement('script');
    newScript.type = 'text/javascript';
    var sourceText = encodeURI(text);
    var source = 'https://www.googleapis.com/language/translate/v2?key=AIzaSyALLIemzcsdQYpyqxAE5k3V7luZ73P5SOQ&target=en&callback=translateText&q=' + sourceText;
    newScript.src = source;
    document.getElementsByTagName('head')[0].appendChild(newScript);
}

function translateText(response){
    globalNodeVar.innerHTML = response.data.translations[0].translatedText;
    globalNodeVar.innerHTML += " <font size='-2'>(google)</font>"; //"&nbsp;<img src='$conf{'htmlRoot'}/html/img/google-g-icon-16.png'>";
    globalNodeVar = 0;
}

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
</script>

STOP

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

print "Content-type: text/html; charset=$conf{'charset'}\n\n";
print "<html>\n<head>\n<title>Resultater</title>\n";
print "<link href=\"", $conf{'htmlRoot'}, "/html/tags.css\" " .
    "rel=\"stylesheet\" type=\"text/css\"></link>";
print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/showtag.js\"></script>\n";
print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/", $corpus, ".conf.js\"></script>\n";

if ($speech_corpus) {
    print $video_scripts;
}

print "\n$googletrans\n\n";
print $style, "\n</head>\n<body>\n";

print <<SCRIPT;

<script type="text/javascript">
function selectAll(Direction)  {
  var chBoxes=document.getElementsByName("delete");
  for(i=0;i<chBoxes.length;i++) {

    if (Direction) {
        chBoxes[i].checked=0;
    }
    else {
        chBoxes[i].checked=1;
    };

  }
}
</script>

SCRIPT

my $media_div = <<STOP;

<div id="inspector" class="inspect">
    <div id="playerpos" style="top:0px;left:0px;position:absolute;width:400px;height:300px">
        <div id='player' class='video'>This text will be replaced</div>
    </div>
    <div class='console' id="ctrl">
        <div class="demo" id="holder">
           <div id="slider-range"></div>
           <div style="float:left;width:24px;position:absolute;left:6px;bottom:3;"><input type="text" id="amountl" style="border:0; color:#ff2200; font-weight:bold;width:24px;background:#000;" /></div>
           <div style="float:left;position:absolute;left:194px;width:12px;height:16px;cursor:pointer;border:0px solid #f00;bottom:3;" id="play" ><img src="http://tekstlab.uio.no/glossa/player/Button-Play-icon.png" style="align:bottom;" /></div>
           <div style="float:right;width:24px;position:absolute;left:378px;bottom:3;"><input type="text" id="amountr" style="border:0; color:#ff2200; font-weight:bold;background:#000;width:20px;" /></div>
       </div>
    </div>
    <div id='scrollbox'></div>
    <div id='pops'></div>
</div>
    <div style="z-index: 1;" id='timecodes'></div>

STOP

if ($speech_corpus) {
    if ($player eq 'qt') {
        print "  <div id=\"inspector\" class=\"inspect\">\n" .
            "    <iframe frameborder='0' width='100%' height='100%' " .
            "id=\"movie_frame\"></iframe>\n" .
            "    <div style=\"position: relative; left: 0px; top: 0px; " .
            "cursor: pointer\" onclick=\"document.getElementById(" .
            "'inspector').style.display='none';\">\n" .
            "      <img alt=\"[x]\" src=\"" . $conf{'htmlRoot'}  .
            "html/img/close.png\" />\n" . 
            "    </div>\n" .
            "  </div>\n<br />\n";
    }
    else {
        print $media_div;
    }
}

my $set_id = CGI::param('set');
my $annotation_in_conf_file;

my $context_type;
my $hlight;

open (CONF, ">/hf/foni/tekstlab/glossa-0.7/dat/engl2/hits/joeljp/conf.txt"); 

my $conf= $conf{'tmp_dir'} . "/" . $query_id . ".conf"; 

print CONF "\$conf = $conf\n";

# FIXME: this is a silly way of doing things
unless (-e $conf) {
  $conf{'tmp_dir'} = $conf{'config_dir'}  . "/" . $corpus . "/hits/"  . $user . "/";
}

if ($hits_name) {
  $conf{'tmp_dir'} = $conf{'config_dir'}  . "/" . $corpus . "/hits/"  . $user . "/";
}

$conf= $conf{'tmp_dir'} . "/" . $query_id . ".conf"; 

print CONF $conf . "\n";
close CONF;
open (CONF, "$conf");

while (<CONF>) {
    chomp;
    if (/^context_type=(.*)/) {
        $context_type=$1;
    }

    if (/^hlight=(.*)/) {
        $hlight=$1;
    }
    
    if (/^name=(.*)/) {
        $hits_name=$1;
    }
    
    if (/^annotation_set=(.*)/) { 
        unless ($set_id) {
            $set_id=$1;
        }

        # if the annotation set isn't specified here, it will be set later
        # (or it will be overridden if it differs from the CGI input)
        $annotation_in_conf_file=1; 
    }
}

close CONF;

my $annotation_select;

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1});

# read multitag file
my %multitags = Glossa::readMultitagFile(%conf);

my $atts = $conf{'corpus_attributes'};
my @atts = split(/ +/, $atts);
shift @atts; # use without "word"

my %tags;

select(STDOUT);
$|=1;

my $corpus_string;
if ($corpus) { $corpus_string = "&corpus=" . $corpus }

my $n = CGI::param('n');
my $del = CGI::param('del');

my $sets_table = uc($corpus) . "annotation_sets";
my $values_table = uc($corpus) . "annotation_values";

my @values;
my $default;

if ($set_id) {
    my $sth = $dbh->prepare(qq{ SELECT default_value FROM $sets_table where id = '$set_id';});
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    ($default) = $sth->fetchrow_array;

    # get values
    my $sth = $dbh->prepare(qq{ SELECT id, value_name FROM $values_table where set_id = '$set_id';});
    $sth->execute  || die "Error fetching data: $DBI::errstr";

    while (my ($id, $name) = $sth->fetchrow_array) {
        push @values, [$id, $name];

    }

    unless ($annotation_in_conf_file) {
        print "appending to $conf<br>";
        open (CONF, ">>$conf");
        print CONF "\n", "annotation_set=", $set_id, "\n";
    }
}

my $top= $conf{'tmp_dir'} . "/" . $query_id . ".top"; 

open (TOP, "$top");

while (<TOP>) {
    if ($del) {
        $_ =~ s/\.cgi\?/.cgi?del=yes&/g;
    }

    #FIXME 
    $_ =~ s/\.cgi\?corpus/.cgi?n=$n&corpus/g;


    # FIXME
    if ($set_id) {
        $_ =~ s/(\">\d+<\/a>)/\&set=$set_id$1/g;
    }
    print;
}

print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/reslist.js\"></script>";
print "<script language=\"javascript\">boldPage($n)</script>";


if ($del) {
    print "<br><br><form action=\"", $conf{'cgiRoot'}, "/delete_hits.cgi\">";
    print "<input type=\"hidden\" name=\"query_id\" value=\"$query_id\">";
    print "<input type=\"hidden\" name=\"n\" value=\"$n\">";
    print "<input type=\"hidden\" name=\"corpus\" value=\"$corpus\"></input>";
    print "<input type=\"hidden\" name=\"player\" value=\"$player\"></input>";
    print "<input type=\"hidden\" name=\"atttype\" value=\"$atttype_copy\"></input>";
    print "<input type=\"submit\" value=\"Delete selection\"></input>";
    print " &nbsp;<input type='button' value='select all' onClick='selectAll(0)'></input>";
    print "<input type='button' value='unselect all' onClick='selectAll(1)'></input>";
    print "&nbsp;&nbsp;&nbsp;&nbsp;<a href='", $conf{'cgiRoot'}, "/show_page_dev.cgi?corpus=$corpus&n=$n&query_id=$query_id'><input value='Finished deleting'></input></a><br>";
}
elsif ($set_id) {
    print "<form action=\"", $conf{'cgiRoot'}, "/save_annotations.cgi\">";
    print "<input type=\"hidden\" name=\"set\" value=\"$set_id\">";
    print "<input type=\"hidden\" name=\"query_id\" value=\"$query_id\">";
    print "<input type=\"hidden\" name=\"corpus\" value=\"$corpus\"></input>";
    print "<input type=\"hidden\" name=\"player\" value=\"$player\"></input>";
    print "<input type=\"hidden\" name=\"atttype\" value=\"$atttype_copy\"></input>";
    print "<br><input type=\"submit\" value=\"Save annotations\"></input>";
    print "&nbsp;(<font color='red'>*</font> indicates: no reviewed value stored.)";
}

my $filename= $conf{'tmp_dir'} . "/" . $query_id . "_" . $n . ".dat"; 

open (DATA, "$filename");

my %tags;

print "<table border='0'>";
 
$/="\n\n\n";

my %video_stars;

if ($speech_corpus) {
    my $sth = $dbh->prepare( "SELECT tid FROM " . uc ( $corpus ) .
                             "author where video = 'Y';");
    $sth->execute  ||  print TEMP "Error fetching data: $DBI::errstr";

    while (my ($v) = $sth->fetchrow_array) {
        $video_stars{$v} = 1;
    }
}

while (<DATA>) {
    my @lines = split(/\n/, $_);
    my $source = shift @lines;
    my ($corp, $s_id, $sts_string, $res_l, $ord, $res_r) = split(/\t/, $source);

		# switching left and right context for right-to-left language corpora
		if ($corpus eq 'quran_mono' and ($context_type eq "chars")) {
				my $r = $res_r;
				$res_r = $res_l;
				$res_l = $r
		}

    my $sts_url = "?" . $corpus_string . "&subcorpus=" . $corp . "&cs=3";

    my @sts = split(/\|\|/, $sts_string);
    my %sts;

    foreach my $sts (@sts) {
        my ($k,$v) = split(/=/, $sts);
        $sts{$k}=$v;
        $sts_url .= "&" . $k . "=" . $v;

    }

    my $t_id = $sts{'text_id'};

    if ($set_id) {
        print "<tr colspan=2><td colspan=2>";

        my $annotation_table = uc($corpus) . "annotations";

        my $start = $sts{'cpos'};
        my $sth = $dbh->prepare(qq{ SELECT value_id FROM $annotation_table where start = '$start' and set_id = '$set_id';});
        $sth->execute  || die "Error fetching data: $DBI::errstr";
        my ($stored_value) = $sth->fetchrow_array;

        if ($set_id eq "__FREE__") {
            print "<input name='annotation_", $start, "' value='", $stored_value, "'></input>";
        }
        else {
            print "<select name=\"annotation_", "$start\"><option value=\"\"></option>"; 
            foreach my $val (@values) {
                print "<option value=\"$val->[0]\"";
                if ($val->[0] == $stored_value) {
                    print " selected"
                }
                elsif (($val->[0] == $default) and !($stored_value)) {
                    print " selected"
                }

                print ">$val->[1]</option>";
            }

            print "</select>";

            unless ($stored_value) {
                print "<font color='red'>*</font>"
            }

        }

        print "<input type='hidden' name='annotationtid_", $start, "' value='", $t_id, "'></input>";
        print "<input type='hidden' name='annotationsid_", $start, "' value='", $s_id, "'></input>";

        print "</td></tr>";

    }

    print "<tr><td height=\"30\"><nobr>";
    my $cpos = $sts{'cpos'};
    
    if ($del) {
        # val was $s_id
        print "<input type='checkbox' name='delete' value='$cpos' />";
    }

    my $identifier = $s_id;

    if ($speech_corpus) {
        $identifier = $sts{text_id};
    }

    my $line_key = $sts{'who_line_key'};
    my $CORPUS = $corpus;
    if($speech_corpus){
        print ("<font size=\"-2\">\n<a href=\"#\" onClick=\"window.open(" .
               "'$conf{'htmlRoot'}/html/profile.php?tid=$identifier&" .
               "corpus=$CORPUS',");
        print ("'mywindow','height=480,width=600,status,scrollbars,resizable');\">" .
               "<img src='$conf{'htmlRoot'}/html/img/i.gif' alt='i' / border='0'>" .
               "</a> \n&nbsp;</font>\n");
    }
    elsif ($CORPUS eq "skriv")
    {
        $identifier = $sts{text_id};
        my $assignment_code = join("_", (split("_", $identifier))[1,2]);
        my $assignment_path = "/michalkk/skriv/oppgavetekster/${assignment_code}.pdf";

        print ("<font size=\"-2\">\n<a href=\"#\" onClick=\"window.open(" .
               "'$conf{'htmlRoot'}/html/profile.php?tid=$identifier&corpus=$CORPUS',");
        print ("'mywindow','height=480,width=600,status,scrollbars,resizable');\">" .
               "<img src='$conf{'htmlRoot'}/html/img/i.gif' alt='i' border='0'>" .
               "</a>&nbsp;</font>");

        if (-e "/var/www/html$assignment_path") {
            printf("<a href=\"$assignment_path\" target=\"_new\"><img " .
                   "src=\"/michalkk/skriv/img/assignment-text.png\" " .
                   "height=\"14\" /></a>&nbsp;");
        }

        my $identifier_noslash = $identifier;
        $identifier_noslash =~ s,/,_,g;
        my $answer_path = "/michalkk/skriv/oppgavesvar/${identifier_noslash}.pdf";
        
        if (-e "/var/www/html$answer_path") {
            printf("<a href=\"$answer_path\" target=\"_new\"><img " .
                   "src=\"/michalkk/skriv/img/assignment-answer.png\" " .
                   "height=\"14\" /></a>");
        }
    }
    else {
        print "<font size=\"-2\"><a href=\"#\" onClick=\"window.open('" .
            $conf{'cgiRoot'} . "/show_context.cgi$sts_url',";
        print "'mywindow','height=500,width=650,status,scrollbars,resizable');\">" .
            "$identifier</a> \n&nbsp;</font>";
    }

    if ($speech_corpus) {
        my $phpfile = 'media3';
        
        if ($player ne 'flash') {
            $phpfile = 'expand';
        }

        my $ex_url = "?corpus=" . $corpus . "&line_key=" . $sts{'who_line_key'} .
            "&size=1&nested=0";
        my $source_line;

        if( $video_stars{ $identifier } ) {

            if($player ne 'flash'){
                $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" " .
                                      "onClick=\"document.getElementById(" .
                                      "'inspector').style.display='block';");
                $source_line.=sprintf("document.getElementById('movie_frame').src " .
                                      "= '$conf{'htmlRoot'}html/" .
                                      "$phpfile.php$ex_url&video=1';\">\n");
                $source_line.=sprintf("<img style='border-style:none' src=" .
                                      "'$conf{'htmlRoot'}html/img/mov.gif'>\n</a>" .
                                      " \n&nbsp;</font>");
            }
            else{
                $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=" .
                                      "\"document.getElementById('inspector')" .
                                      ".style.display='block';");
                $source_line.=sprintf("player = shebang('$CORPUS', '$line_key', " .
                                      "true);\">\n");
                $source_line.=sprintf("<img style='border-style:none' src=" .
                                      "'$conf{'htmlRoot'}html/img/mov.gif'>" .
                                      "\n</a> \n&nbsp;</font>");
            }
        }

        if($player ne 'flash'){
            $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=" .
                                  "\"document.getElementById('inspector')" .
                                  ".style.display='block';");
            $source_line.=sprintf("document.getElementById('movie_frame').src = " .
                                  "'$conf{'htmlRoot'}html/$phpfile.php$ex_url&" .
                                  "video=0';\">\n");
            $source_line.=sprintf("<img style='border-style:none' src=" .
                                  "'$conf{'htmlRoot'}html/img/sound.gif'>\n</a>" .
                                  " \n&nbsp;</font>");
        }
        else{
            $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=" .
                                  "\"document.getElementById('inspector')" .
                                  ".style.display='block';");
            $source_line.=sprintf("player = shebang('$CORPUS', '$line_key'" .
                                  ",false);\">\n");
            $source_line.=sprintf("<img style='border-style:none' src=" .
                                  "'$conf{'htmlRoot'}html/img/sound.gif'>\n</a>" .
                                  " \n&nbsp;</font>");
        }

        $source_line.="<strong>" . $sts{"text_id"} . "</strong>";

        print $source_line;
    }

    print "</nobr></td><td";

    if ($context_type eq "chars") {
        print " align=\"right\"";
    }

    print ">";

    print_it($res_l, $atttype);

    if ($context_type eq "chars") {
        print "</td><td>";
    }

    print "<b> &nbsp;";
    print_it($ord, $atttype);
    print " &nbsp;</b>";

    if ($context_type eq "chars") {
        print "</td><td>";
    }

    print_it($res_r, $atttype);


    print "</td></tr>";###

    if ($parallel) {
        print "<tr><td></td><td";

        if ($context_type eq "chars") {
            print " align=\"right\"";
        }

        print ">";

        print_it($res_l, 2);
        
        if ($context_type eq "chars") {
            print "</td><td>";
        }

        print "<b> &nbsp;";
        print_it($ord, 2);
        print " &nbsp;</b>";

        if ($context_type eq "chars") {
            print "</td><td>";
        }

        print_it($res_r, 2);
        print "</td></tr><tr><td></td><td><br /></td></tr>";###
    }
    
    if (0) {
        my $source_line = "<tr><td></td><td>";
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
        print $source_line;
    }

    if ($speech_corpus) {
        my $orig = get_first($res_l) . "<b>" . get_first($ord) . "</b>" .
            get_first($res_r);
        $orig =~ s/"/_/g;
        $orig =~ s/\#+/&hellip;/g;
        my $source_line .= "<tr><td></td><td>";
        $source_line .= "<div><span onclick=\"appendTranslateScript(" .
            "this.parentNode, '$orig');\" style='font-size:small;cursor:" .
            "pointer;'>[translate]</span></div>";
        $source_line.=sprintf("</td></tr>");
        $source_line .= "<tr><td></td><td></td></tr>";
        print $source_line;
    }

    foreach my $l (@lines) {
        print "<tr><td>";

        my ($corp, $targets, $sts_string, $al) = split(/\t/, $l);

        my $sts_url = "?" . $corpus_string . "&subcorpus=" . $corp . "&cs=3";

        my @sts = split(/\|\|/, $sts_string);
        my %sts;

        foreach my $sts (@sts) {
            my ($k,$v) = split(/=/, $sts);
            $sts{$k}=$v;
            next if ($k eq 's_id');
            $sts_url .= "&" . $k . "=" . $v;
        }

        my $t_id = $sts{'text_id'};

        my @targets = split(/ /, $targets);

        $sts_url .= "&s_id=" . $targets[0];

        foreach my $target (@targets) {
            print "<font size=\"-2\"><a href=\"#\" onClick=\"window.open(" .
                "'", $conf{'cgiRoot'}, "/show_context.cgi$sts_url',";
            print "'mywindow','height=500,width=650,status,scrollbars," .
                "resizable');\">$targets</a> \n&nbsp; </font>";
        }

        print "</td>";

        print "<td";

        if ($context_type eq "chars") {
            print " colspan=\"3\"";
        }

        print ">";

        print "<font color=\"gray\">";
        print_it($al);

        print "<\/font>";
        print "</td></tr>";
    }
}

while (my ($id, $tags) = each %tags) {
    print "<div id=\"$id\" class=\"tag\">$tags</div>";
}
                                   
print "<script language='javascript'>clearCheckBoxes()</script>";
print "</form></table>"; 

## to allow tags to be show at the bottom of the page
print "<br><br><br><br><br><br><br><br><br>";

print "</body></html>";

my $tag_i;

sub get_first{
    my $line = shift;
    $line =~ s/\/[^ ]+//g;
    return $line;
}

sub print_it {
    my $in = shift;
    my $atts_index = shift;
    my @t = split (/ /, $in);

    my $alert = 0;

    foreach my $t (@t) {
        my (@atts_token) = split(/\//, $t);
        my $token_string = $atts_token[$atts_index];

        if ($token_string eq '__UNDEF__') {
            $alert = 1;
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
            if ($a =~ m/_/ or $corpus eq 'run') {
                my $new_a = $multitags{$a}->{$att_token};
                $token_atts .= "<b>" . $new_a . ": </b>" . $att_token . "<br>";		
            }
            else {
                $token_atts .= "<b>" . $a . ": </b>" . $att_token . "<br>";		
            }

        }

        $tag_i++;
        print "<span onMouseOver=\"showTag(arguments[0], \'$tag_i\')\" " .
            "onMouseOut=\"hideTag(\'$tag_i\')\">\n";
        print $token_string, "</span>"; 
        $tags{$tag_i}=$token_atts;
    }
}
