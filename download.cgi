#!/usr/bin/perl

use CGI;
use Spreadsheet::WriteExcel;
use DBI;

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;
use Data::Dumper;

my $corpus=CGI::param('corpus');


my @atts_context = CGI::param('attributes');
my @atts_match = CGI::param('mattributes');
my @atts_aligned = CGI::param('aattributes');

my %hash = map { $_, 1 } @atts_context;
$hash{$_} = 1 foreach ( @atts_match );
my @all_atts = sort keys %hash;

my %conf = GlossaConfig::readConfig($corpus);

my @meta_text = split / /, $conf{'meta_text'};
my @meta_text_name = split / /, $conf{'meta_text'};
if($conf{'meta_text_alias'}){
    $conf{'meta_text_alias'} =~ s/ default//;
    @meta_text_name = split /\t/,  $conf{'meta_text_alias'};
}

my @corpus_attributes = split / /, $conf{'corpus_attributes'};
my @corpus_attributes_name = split / /, $conf{'corpus_attributes'};
if($conf{'corpus_attributes_name'}){
    $conf{'corpus_attributes_name'} =~ s/ default//;
    @corpus_attributes_name = split /\t/,  $conf{'corpus_attributes_name'};
}

my %metas;
@metas{@meta_text} = @meta_text_name;


my $user = $ENV{'REMOTE_USER'}; 
my $query_id = CGI::param('query_id');
my $format = CGI::param('format');

# FIXME: this is a silly way of doing things
my $conf= $conf{'tmp_dir'} . "/" . $query_id . ".conf"; 
unless (-e $conf) {
  $conf{'tmp_dir'} = $conf{'config_dir'}  . "/" . $corpus . "/hits/"  . $user . "/";
}

sub select_parts{
    my $format = shift;
    my $str = shift;
    $str =~ s/__UNDEF__/_/g;
    my @arr = @_;
    my $out;
    my @match = split(/ /, $str);
    my $trs = {};
    foreach my $m (@match){
	next unless $m =~ /[^\s]/;
	my @tmp;
	my @attributes = split /\//, $m;
	foreach my $e (@arr){
	    my $att = $attributes[$e];
	    if($format ne 'html'){
		push @tmp, $att;
		next;
	    }
	    my $attname = $corpus_attributes_name[$e];
	    if($attname =~ /Part_of_speech/){$att =  "<sup>$att</sup>"}
	    $att = "<td>$att</td>";
	    $trs->{$attname} .= $att;
	}
	if($format ne 'html'){$out .= join("/", @tmp) . " "}
    }
    if($format ne 'html'){$out =~ s/ *$//; return $out}
    foreach my $e (@arr){
	my $key = $corpus_attributes_name[$e];
	my $val = $trs->{$key};
	next unless $val;
        $out .=  "\n<tr class=\"textrow $key\">\n$val\n</tr>\n";
    }
    return "<table class=\"texttable\">".$out."</table>";
}

$heredoc = <<END;
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<link rel="shortcut icon" href="http://tekstlab.uio.no/favicon.ico" type="image/ico" />
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<title>Glossa - results</title>
<script src="http://tekstlab.uio.no/glossa-joel-dev/glossa//js/jquery/jquery-1.4.3.min.js" type="text/javascript"></script>
<script type="text/javascript">
    \$( document ).ready(function(){
	\$(".button").click(function(){
	    var classy = \$(this).attr("data-class");
	    \$("."+classy).toggle()
			    });
			 });

</script>
<style type='text/css'>
p{
    font-size: 12px;
    font-family: Helvetica, Arial, Sans-Serif;
    color: #87969D;
}
#box-table-a
{
    font-family: Helvetica, Arial, Sans-Serif;
/*    margin: 45px; */
    width: 100%;
    text-align: right;
    border-collapse: collapse;
}
#box-table-a th
{
    font-size: 13px;
    font-weight: bold;
    padding: 8px;
    background: #f5f5f5; /* #b9c9fe; */
    border-top: 0px solid #000; /* #aabcfe; */
    border-bottom: 0px solid #000;
    color: ##87969D; /* #039; */
}
#box-table-a td
{
    padding: 4px;
    background: #fff; /* #e8edff;  */
    border-bottom: 0px solid #fff;
    /* color: #666;  #669; */
    border-top: 0px solid transparent;
}
#box-table-a tr:hover td
{
    background: #eee; /* #d0dafd; */
}
#box-table-b tr
{
  overflow: scroll;
  display: inline-table;
  width: 100px;
}
.textrow
{
  padding: 0.2em;
  line-height: 30%;
  font-size: 75%;
  text-align: left;
}
.texttable
{
  padding: 0px;
  border: 0px;
  border-spacing: 0px;
}
.tablebox{
  top: 80px;
  left: 50px;
/*  position: fixed; */
  position: absolute;

}
.buttons {
  z-index: 1;
  top: 10;
  left: 50px;
  position: fixed;
  background: #fff;
}
.button{
}
%s
</style>
</head>
<body>
<!--
<div class="buttons">
<p>Toggle visibility: %s</p>
</div>
-->
END
my $style_ids = "";
my $evenodd = 1;
my @colors = ("0854A1", "CF5300", "067014", "9C030D", "4304B0");
foreach my $att (@corpus_attributes_name){
    $att =~ s/^ //;
    $att =~ s/ /_/g;
    $style_ids .= ".$att {  color: #" . $colors[($evenodd++ % 5) - 1] . ";}\n";
}
my $selector = "\n";
$evenodd = 1;
foreach my $att (@all_atts){
    $name = $corpus_attributes_name[$att];
    $data_class = $name;
    $name =~ s/_/ /g;
#    $selector .= "<input type=\"button\" class=\"button\" data-class=\"$data_class\" value=\"$name\" style=\"color: #" . $colors[$evenodd++ -1] . ";\" />\n";
}

$heredoc = sprintf($heredoc, $style_ids, $selector);
print "Content-type: text/html\n\n";

print "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML+RDFa 1.0//EN\" \"http://www.w3.org/MarkUp/DTD/xhtml-rdfa-1.dtd\">\n<html>\n<head>\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n</head>\n<body>\n";

print "Result: ";

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";

$dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1})          ||              die $DBI::errstr;

my $annotation_set = CGI::param('annotationset');

my %annotation_value;
if ($annotation_set) {
    my $annotation_values_table = uc($corpus) . "annotation_values";

    my $sth = $dbh->prepare(qq{ SELECT id,value_name FROM $annotation_values_table where set_id = '$annotation_set';});
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    while (my ($id,$value) = $sth->fetchrow_array) {
	$annotation_value{$id}=$value;
    }    
}

my $out = $query_id . "." . $format;

$query_id = $query_id."_";
my @files = <$conf{'tmp_dir'}/$query_id*>; # AHA!!! There are more than one!!  !!!This doesn't work, as "file_2.txt" > "file_12.txt" joel

my $number_of_files = @files;

# a fix i did way back in the days.. joel
@files = ();
for (my $j = 1; $j <= $number_of_files; $j++ ){
    $files[$j-1] = "$conf{'tmp_dir'}/$query_id" . "$j.dat";
}

print "<a href=\"", $conf{'download_url'}, "/"; 
print $out, "\">", $out, "</a>";

$out = $conf{'dat_files'} . "/"  . $out;
#print "FILEddd: $out<br />";

my $workbook;
if ($format eq "xls") { 
     $workbook = Spreadsheet::WriteExcel->new($out);
    $worksheet = $workbook->add_worksheet();
}


else { open (OUT, ">$out") or die(print "cannot open $out") }

if ($format eq "html") { print OUT "$heredoc\n<div class='tablebox'>\n<table id='box-table-a'>\n<thead>\n"; }


if (CGI::param('head')) {

    my @head;
    my @corpus_structures = CGI::param('corpus_structure');
    foreach my $cat (@corpus_structures) {
	push @head, $cat
    }
    my @meta_values = CGI::param('meta');
    foreach my $cat (@meta_values) {
	push @head, $metas{$cat}
    }
#    push @head, "Attribute";
    if(@atts_context){
	push @head, "Left context";
#	push @head, "<div style='position: fixed; z-index: 1; background: #fff;'>Left context<div>";
	if(@atts_match){ push @head, "match" }
	push @head, "Right context";
    }
    elsif(@atts_match){ push @head, "match" }

# need alignment in header!

    my @acorpus_structures = CGI::param('acorpus_structure');
    foreach my $cat (@acorpus_structures) {
	push @head, $cat
    }
    my @ameta_values = CGI::param('ameta');
    foreach my $cat (@ameta_values) {
	push @head, $cat
    }
    if(@atts_aligned){
	push @head, "Aligned region"
    }

    if ($annotation_set) {
	push @head, "Annotation";
    }
    foreach my $h (@head) {
	$h = ucfirst($h);
    }

    if ($format eq "html") { print OUT "<tr>\n<th>\n", join ("\n</th>\n<th>\n", @head), "\n</th>\n</tr>\n</thead>\n<tbody>\n"; }
    elsif ($format eq "tsv") { print OUT join ("\t", @head), "\n"; }
    elsif ($format eq "csv") {print OUT "\"", join ("\",\"", @head), "\"\n" }
    elsif ($format eq "xls") {

	my $format = $workbook->add_format(); # Add a format
	$format->set_bold();
	$format->set_align('center');

	my $j = 0;
	foreach my $el (@head) {
	    $worksheet->write(0,$j,$el,$format);
	    $j++;
	}

    }
    
}

my $i=0;
if (CGI::param('head')) { $i++ }


my $f_string = "%s";
if($format eq 'html'){ $f_string = "<p>%s</p>" }
foreach my $f (@files) {

    open (FILE, $f); #dat file
    $/="\n\n\n";
    while (<FILE>) {

	my @n;
	my @lines = split(/\n/, $_);
	
	my $source = shift @lines;

	my ($c,$s_id,$sts_string,$left,$match,$right) = split(/\t/, $source);
	my @sts = split(/\|\|/, $sts_string);
	my %sts;
	foreach my $sts (@sts) { #hash all sts_string values, eg text_id=aaseral_04gk..
	    my ($k,$v) = split(/=/, $sts);
	    $sts{$k}=$v;
	}

	my @corpus_structures = CGI::param('corpus_structure');
	foreach my $cat (@corpus_structures) {
	    push @n, sprintf $f_string, $sts{$cat}
	}

	
	my @meta_values = CGI::param('meta');
	foreach my $cat (@meta_values) {
		my $t_id = $sts{'text_id'};
		my $table = uc($corpus) . "text";
		my $sth = $dbh->prepare(qq{ SELECT $cat FROM $table where tid = '$t_id';});
		$sth->execute  || die "Error fetching data: $DBI::errstr";
		my $tm = $sth->fetchrow_array;
		push @n, sprintf $f_string, $tm;
	}
	
=pod	
	my @titles;
	foreach my $e (@all_atts){
	    my $attname = $corpus_attributes_name[$e];
	    push @titles, $attname;
	}


	push @n, sprintf "<table class=\"texttable\"><tr class=\"textrow\"><td>%s</td></tr><tr class=\"textrow\"><td>%s</td><tr class=\"textrow\"><td>%s</td></tr><tr class=\"textrow\"><td>%s</td></tr></table>", @titles;
=cut
	push @n, select_parts($format, $left, @atts_context);

	push @n, select_parts($format, $match, @atts_match);

	push @n, select_parts($format, $right, @atts_context);

	if (CGI::param('align')) {
	    foreach my $a (@lines) {

		my ($c,$s_id,$sts_string,$al) = split(/\t/, $a);
		$s_id =~ /([a-z0-9]+)\..*$/i;
		my $t_id = $1;
		my @sts = split(/\|\|/, $sts_string);
		my %sts;
		foreach my $sts (@sts) {
		    my ($k,$v) = split(/=/, $sts);
		    $sts{$k}=$v;
		}
		#need to change s_id and t_id. they now contain the values for the original text, not the aligned. this NEEDS to be done differently, to make it more general (not just OMC).
		$sts{'s_id'}=$s_id;
		$sts{'text_id'}=$t_id;
		#there. as said, should be done differently!
		my @corpus_structures = CGI::param('acorpus_structure');
		foreach my $cat (@corpus_structures) {
		    push @n, sprintf $f_string, $sts{$cat}
		}

		my @meta_values = CGI::param('ameta');

#found the s_id which contains the tid!
#		$s_id =~ /([a-z0-9]+)\..*$/i;
#		my $tid = $1;
#		my $table = uc($corpus)."s_align";
#		my $src = $sts{'s_id'};
		#don't know where to find tid for translation so doing this. rather round about.
#		my $sth = $dbh->prepare(qq{ SELECT target FROM $table where source = '$src' and lang = 'en';  }); #HERE! NEED TO LOCATE LANG VAR
#		$sth->execute || die "Error fetching data: $DBI::errstr";
#		my $tgt = $sth->fetchrow_array;
#		$tgt =~ s/\..*//;
		foreach my $cat (@meta_values) {
		    my $table = uc($corpus) . "text";
		    my $sth = $dbh->prepare(qq{ SELECT $cat FROM $table where tid = '$t_id';});
		    $sth->execute  || die "Error fetching data: $DBI::errstr";
		    my $tm = $sth->fetchrow_array;
		    push @n, sprintf $f_string, $tm;
		}
		push @n, select_parts($format, $al, @atts_aligned);

	    }
	}

	
	# annotations

	if ($annotation_set) {
	    my $annotation_table = uc($corpus) . "annotations";
	    my $sth = $dbh->prepare(qq{ SELECT value_id FROM $annotation_table where s_id = '$s_id' and set_id = '$annotation_set';});
	    $sth->execute  || die "Error fetching data: $DBI::errstr";
	    my ($stored_value) = $sth->fetchrow_array;

	    my $displayed_value;
	    if ($annotation_set eq '__FREE__') {
		$displayed_value = $stored_value;
	    }
	    else {
		$displayed_value = $annotation_value{$stored_value};
	    }

	    push @n, $displayed_value;
	}

        if ($format eq "html") { print OUT "\n\n\n<!-- HERE -->\n<tr>\n<td>\n", join ("\n\n</td>\n<td align='left'>\n\n", @n), "\n</td>\n</tr>\n</tbody>\n<!-- TO HERE! -->\n\n\n"; }
	elsif ($format eq "tsv") { print OUT join ("\t", @n), "\n" }
	elsif ($format eq "csv") {
	    $out =~ s/\"/\"\"\"/g;
	    my $out = "\"" . join ("\",\"", @n). "\"" . "\n";
	    print OUT $out;
	}
	elsif ($format eq "xls") {

	    my $j=0;
	    foreach my $el (@n) {
		$worksheet->write($i,$j,$el);
		$j++;
	    }
	    $i++;
	}
    }
    close FILE;

}

if ($format eq "html") { print OUT "</div>\n</table>\n</body>\n</html>"; }
