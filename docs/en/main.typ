#import "@preview/orange-book:0.7.1": book

#let horizontalrule = line(length: 100%, stroke: 0.5pt + luma(150))

#show: book.with(
  title: "Wiki of the Master Craftsmen's Schools at Munich East Station (0)",
  author: "Franz Höpfinger",
  date: "2022-2026",
  copyright: [2022-2026, Meisterschulen am Ostbahnhof - München],
  lang: "en",
  main-color: rgb("#3F51B5"),
)

#include "book.typ"
