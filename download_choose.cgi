#!/usr/bin/perl

use CGI;

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

print "Content-type: text/html\n\n";

my $corpus = CGI::param('corpus');

my %conf = GlossaConfig::readConfig($corpus);

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
$dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 0}) || die $DBI::errstr;

my $query_id = CGI::param('query_id');

print "<html><head></head><body>";
my $speech = 0;
if($conf{'corpus_mode'} eq 'speech'){$speech = 1;}

########################################################################
#20130821, similar changes as those made to count_choose.cgi & count.cgi

my @corpus_attributes = split / /,  $conf{'corpus_attributes'};
my @corpus_attributes_name = @corpus_attributes;
if($conf{'corpus_attributes_name'}){
    @corpus_attributes_name = split /\t/,  $conf{'corpus_attributes_name'};
}

my @meta_text = split / /, $conf{'meta_text'};
my @meta_text_name = split / /, $conf{'meta_text'};
if($conf{'meta_text_alias'}){
    @meta_text_name = split /\t/,  $conf{'meta_text_alias'};
}


my @corpus_structures = split / /, $conf{'corpus_structures'};
my @corpus_structures_name = split / /, $conf{'corpus_structures'};
if($conf{'corpus_structures_name'}){
    @corpus_structures_name = split /\t/,  $conf{'corpus_structures_name'};
}



#can't use the hash unfortunately. order is lost causing more hassle than worth..
#keeping it here, as maybe i'll have time to fix it.
=pod
my $corpus_attributes_ref = {};
my $j = 0;
foreach my $k (@corpus_attributes_name){
    if($k eq '_'){$j++; next};
    $corpus_attributes_ref->{$k} = $j++;
}
foreach my $name (keys %$corpus_attributes_ref){
}
=cut
#20130821 end
########################################################################
print "<form action=\"", $conf{'cgiRoot'}, "/download.cgi\" method=\"get\">";
print "<input type=\"hidden\" name=\"query_id\" value=\"$query_id\">";
print "<input type=\"hidden\" name=\"corpus\" value=\"$corpus\">";

print "<input type=\"checkbox\" name=\"head\" checked></input> Create headings<br>";

print "<table cellspacing=\"10\"><tr><td valign=\"top\">";

print "<b>Token data (all):</b><br>\n";

my $i = 0;
foreach my $corpus_attributes_name (@corpus_attributes_name){
    if($corpus_attributes_name eq '_'){	$i++; next }
    my $name = $corpus_attributes_name;
    my $checked = ($name =~ s/ default// ? "checked" : "");
    print "<input type=\"checkbox\" name=\"attributes\" value=\"".$i++."\" $checked></input> " . ucfirst($name) . "<br>\n";
}
print "<b>Token data (match):</b><br>\n";
$i = 0;
foreach my $corpus_attributes_name (@corpus_attributes_name){
    if($corpus_attributes_name eq '_'){	$i++; next }
    my $name = $corpus_attributes_name;
    my $checked = ($name =~ s/ default// ? "checked" : "");
#    my $checked = ($corpus_attributes_name =~ s/ default// ? "checked" : "");
    print "<input type=\"checkbox\" name=\"mattributes\" value=\"".$i++."\" $checked></input> " . ucfirst($name) . "<br>\n";
}
print "</td><td valign=\"top\">";

print "<b>Metadata:</b><br>\n";

$i = 0;
foreach my $name (@corpus_structures_name){
    if($name eq '_'){ $i++; next }
    my $onyma = $name;
    my $checked = ($onyma =~ s/ default// ? "checked" : "");
    print "<input type=\"checkbox\" name=\"corpus_structure\" value=\"".$corpus_structures[$i++]."\" $checked></input> " . ucfirst($onyma) . "<br>\n";
}
$i = 0;
foreach my $name (@meta_text_name){
    if($name eq '_'){ $i++; next }
    my $onyma = $name;
    my $checked = ($onyma =~ s/ default// ? "checked" : "");
    print "<input type=\"checkbox\" name=\"meta\" value=\"".$meta_text[$i++]."\" $checked></input> " . ucfirst($onyma) . "<br>\n";
}
if ($conf{'type'} eq 'multilingual') {
    print "</tr><tr><td valign=\"top\">";
    print "<b><font size=\"+1\"><I>Alignments:</I></font></b><br>";
    print "<input type=\"checkbox\" name=\"align\" checked></input> Include aligmnents";
    
    print "</tr><tr><td valign=\"top\">";
    print "<b>Token data (aligment):</b><br>";

#20130822 more changes, the same generalization utilizing the cgi.conf
    my $i = 0;
    foreach my $corpus_attributes_name (@corpus_attributes_name){
	if($corpus_attributes_name eq '_'){	$i++; next }
	my $name = $corpus_attributes_name;
	my $checked = ($name =~ s/ default// ? "checked" : "");
#	my $checked = ($corpus_attributes[$i] eq 'lemma' ? "checked" : "");
	print "<input type=\"checkbox\" name=\"aattributes\" value=\"".$i++."\" $checked></input> " . ucfirst($name) . "<br>\n";
    }
    print "</td><td valign=\"top\">";
    print "<b>Metadata (alignment):</b><br>";

    $i = 0;
    foreach my $name (@corpus_structures_name){
	if($name eq '_'){ $i++; next }
	my $onyma = $name;
	my $checked = ($onyma =~ s/ default// ? "checked" : "");
	print "<input type=\"checkbox\" name=\"acorpus_structure\" value=\"".$corpus_structures[$i++]."\" $checked></input> " . ucfirst($onyma) . "<br>\n";
    }
    $i = 0;
    foreach my $name (@meta_text_name){
	if($name eq '_'){ $i++; next }
	my $onyma = $name;
	my $checked = ($onyma =~ s/ default// ? "checked" : "");
	print "<input type=\"checkbox\" name=\"ameta\" value=\"".$meta_text[$i++]."\" $checked></input> " . ucfirst($onyma) . "<br>\n";
    }
}

print "</td></tr><tr><td valign=\"top\">";
print "<b>Annotation:</b><br>";
print "<select name=\"annotationset\">";
print "<option value=\"\" selected></option>";
print "<option value=\"__FREE__\">** free annotation **</option>";

my $sets_table = uc($corpus) . "annotation_sets";

# get sets
my $sth = $dbh->prepare(qq{ SELECT id, name FROM $sets_table;});

$sth->execute  || die "Error fetching data: $DBI::errstr";
while (my ($id, $name) = $sth->fetchrow_array) {
    print "<option value=\"$id\">$name</option>";
}
print "</select>";


print "</td></tr></table>";

print "<br>Format: <select name=\"format\"><option value=\"tsv\">Tab separated values</option><option value=\"csv\">Comma separated values</option><option value=\"xls\">Excel spreadsheet</option><option value=\"html\">HTML</option></select><br>";
print "<input type=\"submit\"></input>";
print "</form>";
print "<b>$sets_table</b>";
print "</body></html>";
