#!/usr/bin/perl

use CGI;
use DBI;

use lib ('./lib');
use Glossa_local;
use GlossaConfig;

my $query_id = CGI::param('query_id');
my $corpus = CGI::param('corpus');
my $user = $ENV{'REMOTE_USER'}; 

my %conf = GlossaConfig::readConfig($corpus);

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
$dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 0}) || die $DBI::errstr;

print "Content-type: text/html\n\n";


my $sets_table = uc($corpus) . "annotation_sets";

# update from CGI values
my $newname = CGI::param('newname');
if ($newname) {
    $dbh->do(qq{ insert into $sets_table set name = '$newname'; });
}


## add value
## drop value

## set value as default



print "<html><head></head><body>";
print "<img src='http://omilia.uio.no/img/tri.png' /><br />Due to a bug, results saved prior to 30. March, 2012 may be retrieved incorrectly when using this page.<br />If you experience any problems, contact us at the Text Laboratory.<br /><br />";
print "<table><tr><td valign=top><form action=\"", $conf{'cgiRoot'}, "/annotation_sets.cgi\" method=\"get\">";


print "name: <input name=\"newname\" type=\"text\"></input> <input type=\"submit\" value=\"Create set\"></input> <br>";
print "<input type='hidden' name='corpus' value='$corpus'></input>";

print "</form>";

print "<br><hr><br>";



print "<form action=\"", $conf{'cgiRoot'}, "/edit_set.cgi\" method=\"get\">";
print "<input type='hidden' name='corpus' value='$corpus'></input>";
print "<select name=\"set\">";
# get sets
my $sth = $dbh->prepare(qq{ SELECT id, name FROM $sets_table;});
$sth->execute  || die "Error fetching data: $DBI::errstr";
while (my ($id, $name) = $sth->fetchrow_array) {
    print "<option value=\"$id\">$name</option>";
}
print "</select>";
print " <input type=\"submit\" value=\"Edit set\"></input><br>";
print "</form>";


print "<hr><br>Set statistics for:";

print "<form action=\"", $conf{'cgiRoot'}, "/set_statistics.cgi\" method=\"get\">";
print "<input type='hidden' name='corpus' value='$corpus'></input>";


print "<select name=\"set\">";
my $sth = $dbh->prepare(qq{ SELECT id, name FROM $sets_table;});
$sth->execute  || die "Error fetching data: $DBI::errstr";
while (my ($id, $name) = $sth->fetchrow_array) {
    print "<option value=\"$id\">$name</option>";
}
print "<option value=\"__FREE__\">** free annotation **</option>";
print "</select>";


if ($corpus eq 'nota') {
print "<br>* Group by variable(s)";

print "<select name=\"var\">";
print "<option value=''></option>";
print "<option value='author.sex'>kj&oslash;nn</option>";
print "<option value='author.age'>alder</option>";
print "<option value='author.agegroup'>aldergruppe</option>";
print "<option value='author.bred'>oppvokst</option>";
print "<option value='author.bredreg'>oppvokst (gruppert)</option>";
print "<option value='author.abode'>bor</option>";
print "<option value='author.abodereg'>bor (gruppert)</option>";
print "<option value='author.longest'>bodd lengst</option>";
print "<option value='author.longestreg'>bodd lengst (gruppert)</option>";
print "<option value='author.edu'>utdanning</option>";
print "<option value='author.pro'>yrke</option>";

print "</select>";

print "&nbsp;<select name=\"var2\">";
print "<option value=''></option>";
print "<option value='author.sex'>kj&oslash;nn</option>";
print "<option value='author.age'>alder</option>";
print "<option value='author.agegroup'>aldergruppe</option>";
print "<option value='author.bred'>oppvokst</option>";
print "<option value='author.bredreg'>oppvokst (gruppert)</option>";
print "<option value='author.abode'>bor</option>";
print "<option value='author.abodereg'>bor (gruppert)</option>";
print "<option value='author.longest'>bodd lengst</option>";
print "<option value='author.longestreg'>bodd lengst (gruppert)</option>";
print "<option value='author.edu'>utdanning</option>";
print "<option value='author.pro'>yrke</option>";
print "</select>";


}
elsif ($corpus eq 'upus2') {
print "<br>* Group by variable(s)";
print "<select name=\"var\">";
print "<option value=''></option>";
print "<option value='author.sex'>kj&oslash;nn</option>";
print "<option value='author.agegroup'>aldersgruppe</option>";
print "<option value='author.place'>sted</option>";
print "<option value='author.raised'>oppvokst</option>";
print "<option value='author.parents'>foreldre</option>";
print "<option value='author.lang'>spr&aring;k</option>";
print "<option value='author.langs'>antall&nbsp;spr&aring;k</option>";
print "</select>";

print "&nbsp;<select name=\"var2\">";
print "<option value=''></option>";
print "<option value='author.sex'>kj&oslash;nn</option>";
print "<option value='author.agegroup'>aldersgruppe</option>";
print "<option value='author.place'>sted</option>";
print "<option value='author.raised'>oppvokst</option>";
print "<option value='author.parents'>foreldre</option>";
print "<option value='author.lang'>spr&aring;k</option>";
print "<option value='author.langs'>antall&nbsp;spr&aring;k</option>";
print "</select>";
}


print "<br>* Restrict results to the following saved queries:<br>";

my $hits_dir = $conf{'config_dir'} . "/" . $corpus . "/hits/" . $user . "/";


my @confs = <$hits_dir/*.conf>;
foreach my $conf (@confs) {
    
    my $query_id = $conf;
    $query_id =~ s/\.conf$//;
    $query_id =~ s/.*\///;
    
    my $name;
    open (CONF, $conf);
    while (<CONF>) {
	chomp;
	my ($key,$val) = split(/\s*=\s*/, $_);
	if ($key eq "name") {
	    next unless $val;
	    $name = $val;
	}
    }
    close CONF;
    next unless $name;
    print "<input type='checkbox' name='stored' value='$query_id'></input> $name <br>";
    
}

print "* Value transformations (example: \"N1=N,N2=N,B1=B\")<br>";
print "<input type='text' name='trans' size=50></input><br>";



#meta_text = tid sex agegroup place raised parents lang langs
#meta_text_alias = ID	kj&oslash;nn	aldersgruppe	sted	oppvokst	foreldre	spr&aring;k	spr&aring;

print " <input type=\"submit\" value=\"Get statistics\"></input><br>";



print "</form>";




print "<td width=50>&nbsp;</td>";

print "<td valign='top' width=200 style='background-color:#efefef;border-width:1px;border-style:solid;border-color:#afaeae'>";

print "<b>Help:</b><br>";
print "<p>On this page, you may either <b>create</b> or <b>edit</b> annotation sets. <p>To create one, type the name of the set you would like to create into the text field called 'name' and press 'Create set'.<p> To edit a set, select the relevant one from the drop-down list, and press 'Edit set'.";

print "</td></tr></table>";

print "</body></html>";
