{
  description = "Mixxx DB tools";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.sqlitebrowser
            (pkgs.python3.withPackages (
              ps: with ps; [
                tqdm
                unidecode
                m3u8
                ffmpy
              ]
            ))
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

            function save() {
                cp ~/.mixxx/mixxxdb.sqlite ./mixxxdb.sqlite.backup && \
                cp ./mixxxdb.fixed.sqlite ~/.mixxx/mixxxdb.sqlite
            }
            function load() {
                cp ~/.mixxx/mixxxdb.sqlite ./mixxxdb.sqlite
            }
            function restore() {
                cp ./mixxxdb.sqlite.backup ~/.mixxx/mixxxdb.sqlite
            }
            function next() {
                cp ./mixxxdb.fixed.sqlite ./mixxxdb.sqlite
            }

            function backup() {
                cp ./mixxxdb.sqlite "$(make-unique "./mixxxdb.sqlite.backup.$(date '+%Y-%m-%d')")"
            }
          '';
        };
      }
    );
}
