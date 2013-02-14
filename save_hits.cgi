#!/usr/bin/perl

use CGI;
use File::Copy;
use strict;
use Data::Dumper;

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

select(STDOUT);
$|=1;

print "Content-type: text/html\n\n";

my $corpus=CGI::param('corpus');
my $query_id = CGI::param('query_id');
my $user = $ENV{'REMOTE_USER'}; 
my $name = CGI::param('name');
my $confirm = CGI::param('confirm');
 
my %conf = GlossaConfig::readConfig($corpus);

my %taken_names;
my $hits_dir = $conf{'config_dir'} . "/" . $corpus . "/hits/" . $user . "/";

my @confs = <$hits_dir/*.conf>;

foreach my $conf (@confs) {
    open (CONF, $conf);
    
    while (<CONF>) {
        chomp;
        my ($key,$val) = split(/\s*=\s*/, $_);
        if ($key eq "name") {
            $taken_names{$val}=1;
        }
    }
}

unless ($query_id) {
    die("no query id");
}

if ($taken_names{$name} && !$confirm) {
    print "The name $name is already in use. Hits not saved; " .
        "please select another name.";
    die("The name $name is already in use.");
}

my $orig = $conf{'tmp_dir'} . "/" . $query_id; 
my $new = $conf{'config_dir'} . "/" . $corpus . "/hits/" . $user . "/";

my $new = $conf{'config_dir'} . "" . $corpus . "/hits/" . $user . "/";
unless (-e $new) {
    mkdir($new);
}


# change .conf: add name
my $c = $orig . ".conf";

open (CONF, ">>$c") or die "couldn't open $c";
print CONF "\nname=", $name, "\n";
close CONF;

local $/ = undef;
my $t = $orig . ".top";

open(TOP, "<$t") or die "Can't open old $t";
my $content = <TOP>;
close TOP;

open(TOP, ">$t");
my $repl = "player=flash&name=$name'>save hits<";
$content =~ s/player=flash'>save hits</$repl/;
$repl = "&name=$name'>delete hits";
$content =~ s/'>delete hits/$repl/;
print TOP $content;
close TOP;

my @files=<$orig*>;

my $warning;

foreach my $f (@files) {
    my $n = $f;
    $n =~ s|.*/||;
    $n = $new . $n;
    my $ok = copy($f,$n);

    unless ($ok) {
        print "WARNING: could not copy $f to $n<br>";
        $warning = 1;
    }
}

unless ($warning) {
    print "The results have been saved. Hit the 'back' button on your " .
        "browser to return to your results.";
}
