// SPDX-License-Identifier: BSD-3-Clause
// Compile ONLY this provider translation unit for the capacity-connected bench.
// Native callbacks carry addresses/data, not cache/fetch tags: those immutable
// services remain in SV with full 64-bit request/pending/replay/response storage.
// Reusing the accepted provider body preserves its separately counted live and
// assertion-only work. It neither regenerates nor exports native reference gold.
#include "dataset_capacity_native.hpp"
#include "../../hash/tests/dataset_lifecycle_source_vpi.cpp"
