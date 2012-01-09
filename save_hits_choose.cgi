#!/usr/bin/perl

use CGI;
use File::Copy;
use strict;

use lib("/home/httpd/html/glossa/pm");
use Glossa_old;




select(STDOUT);
$|=1;

print "Content-type: text/html\n\n";

my $corpus=CGI::param('corpus');
my $query_id = CGI::param('query_id');
my $name = CGI::param('name');
my $user = $ENV{'REMOTE_USER'}; 

my $conf = Glossa::get_conf_file($corpus);
my %conf = %$conf;

print "<form action='", $conf{'cgiRoot'}, "/save_hits.cgi' method='GET'>\n";
print "<input type='hidden' name='corpus' value='$corpus' />\n";
print "<input type='hidden' name='query_id' value='$query_id' />\n";


if($name){
    print "<b>Save file: $name</b><br />";
    print "<input type='hidden' name='name' value='$name' />\n";
    print "<input type='hidden' name='confirm' value='yes' />\n";
    print "<input type='submit' value='Confirm'/>\n";
}

else{

    print "<table border='0'>\n<tr>\n<td valign='top'>\n<br>\n";

    print "<input name='name' /> name of results set<br><br>\n";
    print "<input type='submit' value='Save results'/>\n";
    
    print "<br><br><b>Previous names:</b><br>\n";

    my $root = $conf{'config_dir'} . "/" . $corpus . "/hits/" . $user . "/";

    my @files=<$root*.conf>;
    foreach my $f (@files) {
	open(FILE, $f);
	while (<FILE>) {
	    if (/^name ?=(.*)/) {
		print "$1<br>";
		last;
	    }
	}
    
    }

    print "</td>\n<td width=50>&nbsp;</td>\n";
    
    print "<td valign='top' width=200 style='background-color:#efefef;border-width:1px;border-style:solid;border-color:#afaeae'>\n";

    print "<b>Help:</b><br>\n";
    
    print "<p>To save a set of results, you must give them a name; so it can be retrieved easily later.";

    print "</td>\n</tr>\n</table>\n";

}

print "</form>\n";
