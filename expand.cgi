#!/usr/bin/perl

# probably not in use and superseded by expand.php/js

use strict;
use CGI;
use DBI;
use POSIX;

my $cgi = CGI->new;

print "Content-type: text/html\n\n";


# fetch the parameters
my $id = CGI::param('line_key');  # the sql-table key for the segment returned by CQP
my $size = CGI::param('size');    # the context width
my $video = CGI::param('video');  # video?
my $nested = CGI::param('nested');#
if($size>0){$size++;}             # 0 makes no sense
                                  #
my $bottom;                       # to hold id of the first segment within range
my $top;                          # --------""------- last  --------""----------
my $session;                      # to hold the name of the transcriber file



my $db = CGI::param('db');
my $table  = CGI::param('table');

if(!$table){ $table = 'segments'; }

my $database = 'DBI:mysql:database='.$db.';host=omilia.uio.no';

my $dbh=DBI->connect($database, 'joeljp', 'tuba',
		  {RaiseError => 1, AutoCommit => 1});

my $notacgibin="http://omilia.uio.no/cgi-bin/glossa/";

# couple of holders
my @array;
my $hashref;

# bit o' sql
my $SQ="SELECT * FROM $table WHERE id >= $id-$size AND id <= $id+$size";
my $fn="SELECT audio_file FROM $table WHERE id = $id";

# establish file name
$dbh->do($fn);
my $sth=$dbh->prepare($fn);
$sth->execute;
@array=$sth->fetchrow_array();
$fn=$array[0];
$session=$fn;
$fn=filename($fn,$video); # prepare audio file name.

if( $db eq 'upus' ){ $fn = "upus/".$fn; }

# need to check that all segments in range are from
# the same transcription, ie have same file name:)
# if not, adjust range.

$dbh->do($SQ);
$sth=$dbh->prepare($SQ);
$sth->execute;

# set lower limit, ie loop until audio_file matches
while($hashref=$sth->fetchrow_hashref()){
    my $f=$hashref->{"audio_file"};
    if($f ne $session){next;}
    $bottom=$hashref->{"id"};
    last;
}

# loop condition is different, as we want to use the
# existing db row in the first iteration.
# set upper limit, ie loop until audio_file doesn't
# match
my $test = "$session";
while($hashref){
    my $f=$hashref->{"audio_file"};
    if($f eq $session){
	$top=$hashref->{"id"};
	$test.=" $top";
	$hashref=$sth->fetchrow_hashref();
	next;
    }
    last;
}

# obtain the start time code from the first segment
# and the stop time code from the last segment
# convert to QuickTime 30 f/s format
my $start="SELECT begin FROM $table WHERE id = $bottom";
my $stop="SELECT end FROM $table WHERE id = $top";

$dbh->do($start);
$sth=$dbh->prepare($start);
$sth->execute;
@array=$sth->fetchrow_array();
$start=$array[0];
my $QTstart=sec2QTcode($start);

$dbh->do($stop);
$sth=$dbh->prepare($stop);
$sth->execute;
@array=$sth->fetchrow_array();
$stop=$array[0];
my $QTstop=sec2QTcode($stop);

# fetch the range, using the tested upper and lower
# limits
my $SQL="SELECT * FROM $table WHERE audio_file LIKE '$session' AND begin >= $start AND end <= $stop";
$dbh->do($SQL);
$sth=$dbh->prepare($SQL);
$sth->execute;

# the movie object for embedding
my $obj = <<EMBED_END;
<object CLASSID='clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B' 
width='320' height='256' CODEBASE='http://www.apple.com/qtactivex/qtplugin.cab' 
id='QTplayer'>\n
<param name='src' value='QuickTime4_Required.mov'>\n
<param name='qtsrc' value='rtsp://lillestroem.uio.no/hf/ilf/$fn'>\n
<param name='starttime' value='$QTstart'>\n
<param name='endtime' value='$QTstop'>\n
<param name='autoplay' value='true'>\n
<param name='loop' value='false'>\n
<param name='controller' value='true'>\n
<embed src='http://lillestroem.uio.no/hf/ilf/test.mov' 
qtsrc='rtsp://lillestroem.uio.no/hf/ilf/$fn' starttime='$QTstart'
endtime='$QTstop' width='320' height='256' autoplay='true' 
loop='false' controller='true' pluginspage='http://www.apple.com/quicktime/' 
name='QTplayer'>\n
</embed>\n
</object><br />\n
EMBED_END

# the movie object for embedding
my $obj2 = <<FIX_END;
<script language="JavaScript" type="text/javascript">\n
  QT_WriteOBJECT('QuickTime4_Required.mov', '320', '256', '',\n
    'autoplay', 'true',\n
    'emb#bgcolor', 'black',\n
    'align', 'middle',\n
    'starttime', '$QTstart',\n
    'endtime', '$QTstop',\n
    'autoplay', 'true',\n
    'loop', 'false',\n
    'controller', 'false',
    'qtsrc','rtsp://lillestroem.uio.no/hf/ilf/$fn' 
);\n
</script>\n
FIX_END

# the movie object for embedding
my $obj3 = <<FIXIT_END;
<script language="JavaScript" type="text/javascript">\n
  QT_WriteOBJECT('rtsp://lillestroem.uio.no/hf/ilf/$fn', '320', '256', '',\n
    'autoplay', 'true',\n
    'emb#bgcolor', 'black',\n
    'align', 'middle',\n
    'starttime', '$QTstart',\n
    'endtime', '$QTstop',\n
    'autoplay', 'true',\n
    'loop', 'false',\n
    'controller', 'false',
    'src','QuickTime4_Required.mov' 
);\n
</script>\n
FIXIT_END

###

my $obj___ = <<NUVVA_FIX;
<script language="JavaScript" type="text/javascript">\n
QT_WriteOBJECT(
  "rtsp://lillestroem.uio.no/hf/ilf/$fn", "320", "256", "",
  "autoplay","true",
  "align","middle",
  "starttime","$QTstart",
  "endtime","$QTstop",
  "qtsrc", "rtsp://lillestroem.uio.no/hf/ilf/$fn"\n
);
</script>\n
NUVVA_FIX


# the movie object for embedding
my $obj__ = <<DOCWRITE_END;
<script language="JavaScript" type="text/javascript">\n
    document.write("<object ");
    document.write("CLASSID='clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B' ");
    document.write("width='320' height='256' ");
    document.write("CODEBASE='http://www.apple.com/qtactivex/qtplugin.cab' ");
    document.write("id='QTplayer'>");
    document.write("<param name='src' value='QuickTime4_Required.mov'>");
    document.write("<param name='qtsrc' value='rtsp://lillestroem.uio.no/hf/ilf/$fn'>");
    document.write("<param name='starttime' value='$QTstart'>");
    document.write("<param name='endtime' value='$QTstop'>");
    document.write("<param name='autoplay' value='true'>");
    document.write("<param name='loop' value='false'>");
    document.write("<param name='controller' value='true'>");
    document.write("<embed src='http://lillestroem.uio.no/hf/ilf/test.mov'");
    document.write("qtsrc='rtsp://lillestroem.uio.no/hf/ilf/$fn' starttime='$QTstart'");
    document.write("endtime='$QTstop' width='320' height='256' autoplay='true'");
    document.write("loop='false' controller='true' pluginspage='http://www.apple.com/quicktime/'");
    document.write("name='QTplayer'");
    document.write("></em"+"bed>"+"</obj"+"ect"+">");
</script>\n
DOCWRITE_END

# the html
print <<headEnd;
<html>\n
<head>\n
<meta http-equiv="content-type" content="text/html; charset=ISO-8859-1" />\n
<link rel="shortcut icon" href="http://omilia.uio.no/favicon.ico" type="image/ico" />\n
<style type=\"text/css\">\@import url('http://omilia.uio.no/css/nota/main.css');</style>\n
<style type=\"text/css\">\@import url('http://omilia.uio.no/css/nota/topframe.css');</style>\n
<script type="text/javascript" src="http://omilia.uio.no/js/nota/toggleInfo.js"></script>\n
<script type="text/javascript" src="http://omilia.uio.no/js/nota/QT.js"></script>\n
<script src="http://omilia.uio.no/js/nota/AC_QuickTime.js" language="JavaScript" type="text/javascript"></script>\n
</head>\n\n
<body class=\"topframe\">\n
headEnd

my $url=sprintf("%s%s?line_key=%s&video=%s&db=%s&table=%s&size=",$notacgibin,"expand.pl",$id,$video,$db,$table);

if(!$nested) {
    print "<div class=\"ctrl\">";
    print "<div class=\"div\">";
    print "<strong>Kontekst:</strong><br />&#177; tur: ";
    print "<select id=\"\" name=\"\" class=\"\" size=\"1\" " .
        "onchange=\"window.location='$url'+this.value+''\">";
    print "<option value=\"\">-</option>";
    for(my $i=1;$i<30;$i++){
        print "<option value=\"$i\">$i</option>";
    }
    print "</select><br />\n";
    print "</div>";
    print "<br /><div class=\"div\">\n";
    if($video ne "no"){
        print "<strong>Video:</strong><br />";
        print "<span style=\"cursor: pointer;\" " .
            "onclick=\"javascript:replay(document.QTplayer);\">" .
            "<img src=\"http://omilia.uio.no/img/qtp.png\" /></span><br /><br />\n";
        print "<select id=\"\" name=\"start\" class=\"\" size=\"1\" ". 
            "onchange=\"javascript:restart(document.QTplayer, this.value*1);" .
            "this.value=0;\">";
        print "<option value=\"0\">-</option>\n";
        for(my $j=-5;$j<6;$j++){
            printf("<option value=\"%d\">%d</option>\n",$j*100,$j);
        }
        print "</select><br />\n";
        print "<select id=\"\" name=\"end\" class=\"\" size=\"1\" ".
            "onchange=\"javascript:reend(document.QTplayer, this.value*1);" .
            "this.value=0;\">";
        print "<option value=\"0\">-</option>\n";
        for(my $j=-5;$j<6;$j++){
            printf("<option value=\"%d\">%d</option>\n",$j*100,$j);
        }
        print "</select><br />\n";
    }
    print "</div>\n";
    print "</div>\n";
    print "<div class=\"txt\">\n";
    if($size>3){
        print "<iframe name=\"text\" frameborder=\"0\" width=\"500\" " .
            "height=\"256\" ".
            "scrolling=\"auto\" src=\"$url$size&nested=yes\">\n</iframe>\n";
    }
}
if($size<=3||$nested){
    print "<table class=\"res\" width=\"100%\" border=\"0\">\n<tr>\n";
    print tablefill($sth);
    print "</table>\n";
}

if(!$nested){
    print "</div>\n";
    print "<div class=\"mov\">";
    if($video ne "no"){
	print "$obj";
    }
    print "</div>";
}
print "</body></html>\n";

$sth->finish;
$dbh->disconnect;

sub tablefill{
    my ($sth)=shift;
    my $hashref;
    my $fill="";
    my $color="#000000";
    my $bgcolor="#ffffff";
    my $last_ref=0;
    while($hashref=$sth->fetchrow_hashref()){
	my $ref=$hashref->{"ref"};
	my $seg=$hashref->{"seg"};
	my $begin=$hashref->{"begin"};
	my $end=$hashref->{"end"};
	$seg=tidyTags($seg);

	if($ref ne $last_ref) {
	    if($bgcolor eq "#ffffff") {
          $bgcolor="#aaddff";
      }
	    else {
          $bgcolor="#ffffff";
      }
	}

	if($hashref->{"id"} eq $id){$color="#cc2222";}
	else{$color="#000000";}
	$fill .= "<tr valign=\"top\" bgcolor=\"$bgcolor\">\n<td>$ref</td>".
	         "<td><font color=\"$color\">$seg</font></td>\n</tr>\n";
	$last_ref=$ref;
    }
    return $fill;
}

# removes initials, adds suffix.
sub filename{
    my $fn=shift;
    my $v=shift;
    $fn=~s/[A-Z]*_?//;
    if($v eq "audio"){return "lyd/".$fn.".mov";}
    return $fn."_320kbps.mov";
}

# converts time code to quicktime format.
sub sec2QTcode{
    my $arg = shift;
    if($arg > 0){
	my $QTS = $arg;
	$QTS =~ /([0-9]+\.[0-9]{1,3})/;
	$arg = $1;
    }
    my @time=split(/\./,$arg);
    my ($hour,$min,$sec,$dec);
    ($hour, $min) = divSplit($time[0], 3600);
    ($min, $sec) = divSplit($min, 60);
    $dec = $time[1];

    # must be three digits. ie this is to the right of the decimal point.
    if($dec =~ /^\d\d$/) {
        $dec = $dec."0";
    }
 
    $dec = floor($dec/(1000/30));
    
    return sprintf "%.2d:%.2d:%.2d:%.2d",$hour,$min,$sec,$dec;
}

# divide $num by $divisor, putting result and remainder in @res
sub divSplit { 
    my ($num, $divisor)=@_;
    my @res;
    my $rem=$num % $divisor;
    my $n = floor($num / $divisor);
    push(@res, $n);
    push(@res, $rem);
    return @res;
}

sub tidyTags {
    my $str=shift;
    my @toks = split /\]\[/, $str;
    my @arr;
    my $out = "";

    foreach my $tok(@toks){

        $tok =~ s/[\[\]]//g;
        @arr = split /\|/, $tok;

        $out .= $arr[0]." ";

    }

    $out =~ s/&amp;/&/g;
    return $out;
}
