{ nixpkgs ? (import <nixpkgs> {}).fetchFromGitHub {
    owner  = "NixOS";
    repo   = "nixpkgs";
    rev    = "d0d905668c010b65795b57afdf7f0360aac6245b";
    sha256 = "1kqxfmsik1s1jsmim20n5l4kq6wq8743h5h17igfxxbbwwqry88l";
  }}:

with import nixpkgs {};

stdenv.mkDerivation rec {
  name = "dev";
  buildInputs = [
    (python.withPackages (ps: with ps; [
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
