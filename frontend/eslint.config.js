import js from "@eslint/js";
import typescript from "@vue/eslint-config-typescript";
import vue from "eslint-plugin-vue";

export default [
  { ignores: ["dist/**", "node_modules/**"] },
  js.configs.recommended,
  ...vue.configs["flat/recommended"],
  ...typescript(),
];
