{
  rev ? "d032c1a6dfad4eedec7e35e91986becc699d7d69", # nixos-24.05 incl CVE-2024-6387 fix
  sha256 ? "14g286p6dh0j1qbkmw2520si2lbbjmbmr119496jkmpk6516n3v7",
  nixpkgs    ? builtins.fetchTarball {
    name   = "nixpkgs-${rev}";
    url    = "https://github.com/nixos/nixpkgs/archive/${rev}.tar.gz";
    sha256 = sha256;
  }
}:

with import nixpkgs {};

stdenv.mkDerivation rec {
  name = "dev";
  buildInputs = [
    sqlitebrowser
    (python3.withPackages (ps: with ps; [
      tqdm
      unidecode
      m3u8
      ffmpy
    ]))
  ];
  shellHook = ''
    export REPO_ROOT=`dirname ${toString ./default.nix}`
    export PYTHONIOENCODING=utf8
    addToSearchPath PATH "$REPO_ROOT"

    function make-unique() {
        name=$1
        if [[ -e $name || -L $name ]]
        then
            i=0
            while [[ -e $name-$i || -L $name-$i ]] ; do
                let i++
            done
            name=$name-$i
        fi
        echo $name
    }

    alias save="cp ~/.mixxx/mixxxdb.sqlite ./mixxxdb.sqlite.backup && \
                cp ./mixxxdb.fixed.sqlite ~/.mixxx/mixxxdb.sqlite"
    alias load="cp ~/.mixxx/mixxxdb.sqlite ./mixxxdb.sqlite"
    alias restore="cp ./mixxxdb.sqlite.backup ~/.mixxx/mixxxdb.sqlite"
    alias next="cp ./mixxxdb.fixed.sqlite ./mixxxdb.sqlite"

    function backup() {
        cp ./mixxxdb.sqlite "$(make-unique "./mixxxdb.sqlite.backup.$(date '+%Y-%m-%d')")"
    }
  '';
}
