{
  rev        ? "72d8853228c9758820c39b8659415b6d89279493",
  sha256     ? "10r5zh0052apd90riimaly2xc9d4w5p9g81s9nhjk12kirf6ihcs",
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
    ]))
  ];
  shellHook = ''
    export REPO_ROOT=`dirname ${toString ./default.nix}`
    export PYTHONIOENCODING=utf8
    addToSearchPath PATH "$REPO_ROOT"

    alias save="cp ~/.mixxx/mixxxdb.sqlite ./mixxxdb.sqlite.backup && \
                cp ./mixxxdb.fixed.sqlite ~/.mixxx/mixxxdb.sqlite"
    alias load="cp ~/.mixxx/mixxxdb.sqlite ./mixxxdb.sqlite"
    alias restore="cp ./mixxxdb.sqlite.backup ~/.mixxx/mixxxdb.sqlite"
    alias next="cp ./mixxxdb.fixed.sqlite ./mixxxdb.sqlite"
  '';
}
