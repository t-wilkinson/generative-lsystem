with import <nixpkgs> {};
mkShell {
  buildInputs = [
    (with pkgs.python3Packages; [ pyglet numpy ])
  ];
}
