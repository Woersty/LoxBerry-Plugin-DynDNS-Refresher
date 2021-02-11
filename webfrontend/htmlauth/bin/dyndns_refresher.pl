#!/usr/bin/perl
# Call PHP
use Data::Dumper;
use File::Basename;
use strict;
use warnings;
use Cwd 'abs_path';
our $psubfolder = abs_path($0);
$psubfolder =~ s/(.*)\/(.*)\/bin\/(.*)$/$2/g;
system("php -f ".dirname(dirname(dirname(dirname(dirname(abs_path($0))))))."/html/plugins/$psubfolder/index.php");
