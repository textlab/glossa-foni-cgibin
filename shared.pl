# Shared code between cgi scripts. Should be moved to the Glossa module
# in the future.

# reading the main and corpus config files
# returns a hash of the key=value pairs in the file.
sub readConfigFile {
    my ($fn) = @_;

    my %conf;
    open (CONF, $fn);
    while ( <CONF> ) {
        chomp;
        next if (/^\#/);
        s/\s*$//;
        my ($k,$v)=split(/\s*=\s*/);
        $conf{$k}=$v;
    }
    close CONF;

    return %conf;
}

sub getRootURIPath {
    my $path = $ENV{REQUEST_URI};
    my @parts = split("/", $path);
    
    return join("/", @parts[2..($#parts-2)]);
}

1;
