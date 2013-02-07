package Glossa::test;

use strict;
use Test::Simple tests => 6;

use lib ('..');
use Glossa_local;

ok(Glossa::trimString('    ') eq '');
ok(Glossa::trimString('    ba  ') eq 'ba');

my $test_config_fn = 'data/paths.conf.test';
my %result = Glossa::readConfigFile($test_config_fn);

ok((scalar keys %result) == 2);
ok($result{'ba'} eq 'foo');
ok($result{'knark'} eq 'fnork');

my $media_div = <<STOP;
<div class="inspect" id="inspector">
    <div style="top:0px;left:0px;position:absolute;width:400px;height:300px" id="playerpos">
        <div class="video" id="player">Loading player...</div>
    </div>
    <div class="console" id="ctrl">
        <div class="demo" id="holder">
           <div id="slider-range"></div>
           <div style="float:left;width:24px;position:absolute;left:6px;bottom:3;"><input style="border:0; color:#ff2200; font-weight:bold;width:24px;background:#000;" type="text" id="amountl" /></div>
           <div style="float:left;position:absolute;left:194px;width:12px;height:16px;cursor:pointer;border:0px solid #f00;bottom:3;" id="play" ><img src="/player/Button-Play-icon.png" style="align:bottom;" /></div>
           <div style="float:right;width:24px;position:absolute;left:378px;bottom:3;"><input style="border:0; color:#ff2200; font-weight:bold;background:#000;width:20px;" type="text" id="amountr" /></div>
       </div>
    </div>
    <div id="scrollbox"></div>
    <div id="pops"></div>
    </div> 
    <div style="z-index: 1;" id="timecodes"></div>
STOP

$media_div =~ s/\s+//g;
my %conf = ('htmlRoot', '');
my $media_div_result = Glossa::create_media_div(%conf);
$media_div_result =~ s/\s+//g;

ok($media_div eq $media_div_result);
