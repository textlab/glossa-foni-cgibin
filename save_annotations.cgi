#!/usr/bin/perl

use CGI;
use DBI;
use strict;

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

my $corpus = CGI::param('corpus');
my $set = CGI::param('set');
my $user = $ENV{'REMOTE_USER'}; 

my %conf=GlossaConfig::readConfig($corpus);

my $hits_dir = $conf{'config_dir'} . "/" . $corpus . "/hits/" . $user . "/";

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1});

print "Content-type: text/html\n\n";
print "<html><head></head><body>";

my @names = CGI::param;

my $annotations_table = uc($corpus) . "annotations";

my %anno;
foreach my $name (@names) {
    
    my $value = CGI::param($name);

    if ($name =~ s/^annotation_//) {
	print "$name <b>$value</b><br>";
	$anno{$name}->{'value'}=$value;
    }

    if ($name =~ s/^annotationsid_//) {
	print "$name <b>$value</b><br>";
	$anno{$name}->{'s_id'}=$value;
    }

    if ($name =~ s/^annotationtid_//) {
	print "$name <b>$value</b><br>";
	$anno{$name}->{'tid'}=$value;
    }

}

while (my ($k,$v) = each %anno) {


    my $start = $k;

    my %keys = %$v;

    my $value = $keys{'value'};
    my $s_id = $keys{'s_id'};
    my $tid = $keys{'tid'};

    my $sth = $dbh->prepare("SELECT id FROM $annotations_table where start = '$start' and set_id = '$set';");
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    my ($id) = $sth->fetchrow_array;
    

    if ($id) {
	$dbh->do("update $annotations_table set start = '$start',s_id='$s_id',tid='$tid',value_id='$value',set_id='$set' where id = '$id';");
    }
    else {
	$dbh->do("insert into $annotations_table set start = '$start',s_id='$s_id',tid='$tid',value_id='$value',set_id='$set';");	
    }
    


}

print "</body></html>";


