with import <nixpkgs> {};
mkShell {
  buildInputs = [
    (with pkgs.python35Full; [ pyglet numpy ])
  ];
}
