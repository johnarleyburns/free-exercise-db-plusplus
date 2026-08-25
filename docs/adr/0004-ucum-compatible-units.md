# ADR 0004: Explicit compatible units

Status: accepted

Quantities retain their source unit. Derived analysis may convert only known
compatible units and must preserve missing or unknown values rather than guess.
The interchange layer remains permissive enough for extensions; analysis is
conservative at its conversion boundary.
