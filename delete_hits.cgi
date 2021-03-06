#!/usr/bin/perl

use CGI;
use File::Copy;
use strict;

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

select(STDOUT);
$|=1;

print "Content-type: text/html\n\n";

my $corpus=CGI::param('corpus');
my $player=CGI::param('player');
my $atttype=CGI::param('atttype');
my $user = $ENV{'REMOTE_USER'}; 

my %conf = GlossaConfig::readConfig($corpus);

my $n = CGI::param('n');
my $query_id = CGI::param('query_id');


# FIXME: this is a silly way of doing things
my $conf= $conf{'tmp_dir'} . "/" . $query_id . ".conf"; 
unless (-e $conf) {
  $conf{'tmp_dir'} = $conf{'config_dir'}  . "/" . $corpus . "/hits/"  . $user . "/";
}

my @params = CGI::param('delete');

my %to_delete;
foreach my $p (@params) {
    $to_delete{$p}=1;
}
 

my $filename= $conf{'tmp_dir'} . "/" . $query_id . "_" . $n . ".dat"; 
open (DATA, "$filename");

my $filename_n=$conf{'tmp_dir'} . "/"  . $query_id . "_" . $n . ".tmp"; 
open (NEW, ">$filename_n");


$/="\n\n\n";

while (<DATA>) {
    my $line = $_; 
    my @lines = split(/\n/, $_);

    my $source = shift @lines;

    my ($corp, $s_id, $sts_string, $res_l, $ord, $res_r) = split(/\t/, $source);
    $sts_string =~ /cpos=(\d+)/;
    my $cpos = $1;
    unless ($to_delete{$cpos}) {
        print NEW $_;
    }
}

close DATA;
close NEW;

move($filename_n,$filename);

print "Please select:<br>";
print "<a href='", $conf{'cgiRoot'}, "/show_page_dev.cgi?corpus=$corpus&n=$n&query_id=$query_id&player=$player&atttype=$atttype'>Finished deleting</a><br>";

print "<a href='", $conf{'cgiRoot'}, "/show_page_dev.cgi?corpus=$corpus&n=$n&query_id=$query_id&del=yes&player=$player&atttype=$atttype'>Delete more hits on same page</a><br>";

my $m = $n+1;
my $filenamem=$conf{'tmp_dir'} . "/"  . $query_id . "_" . $m . ".dat"; 
if (-e $filenamem) {
 print "<a href='", $conf{'cgiRoot'}, "/show_page_dev.cgi?corpus=$corpus&n=$m&query_id=$query_id&del=yes&player=$player&atttype=$atttype'>Delete hits on next page</a><br>";
}
