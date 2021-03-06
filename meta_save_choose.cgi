#!/usr/bin/perl

use CGI;
use DBI;
use Data::Dumper;
use strict;

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

select(STDOUT);
$|=1;

print "Content-type: text/html\n\n";
print "<html><head></head><body>";






my $cgi = CGI->new;

my %in = Glossa::create_params();

my $CORPUS = $in{'query'}->{'corpus'}->[0];
my $base_corpus = $in{'phrase'}->{'0'}->{'corpus'}->[0];

my %conf = GlossaConfig::readConfig($CORPUS);

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 0}) || die $DBI::errstr;

my $format = CGI::param('format');


my $tablename = $base_corpus . "_lexstat";


my ($subcorpus,$sql_query_nl,$texts_allowed,$subcorpus_string) = Glossa::create_tid_list(\%conf, \%in, $CORPUS);

if ($subcorpus_string) {

    print "<pre>";
    print $subcorpus_string;
    print "</pre>";
    
    # save string
    my $fname = "/tmp/meta_" . int(rand 100000) . ".dat";

    open (TMP, ">$fname");
    print TMP $subcorpus_string;
    close TMP;

    # print form

    print "<form action='", $conf{'cgiRoot'}, "/meta_save.cgi' method='get'>\n";
    print "<input type='text' name='subcorpus_name'></input>\n";
    print "<input type='hidden' name='subcorpus_id' value='$fname'></input>\n";
    print "<input type='hidden' name='corpus' value='$CORPUS'></input>\n";
    print "<input type='submit'></input>\n";
    print "</form>";

    

}
else {
    print "<b>No selection to save.</b>";
}

