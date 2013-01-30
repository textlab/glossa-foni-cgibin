package Glossa::test;

use strict;
use Test::Simple tests => 5;

use lib ('..');
use Glossa_local;

ok(Glossa::trimString('    ') eq '');
ok(Glossa::trimString('    ba  ') eq 'ba');

my $test_config_fn = 'data/paths.conf.test';
my %result = Glossa::readConfigFile($test_config_fn);

ok((scalar keys %result) == 2);
ok($result{'ba'} eq 'foo');
ok($result{'knark'} eq 'fnork');
