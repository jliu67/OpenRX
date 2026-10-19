// SPDX-License-Identifier: BSD-3-Clause
// Capacity-only native adapter. The accepted prepared context, algorithms and
// counters stay unchanged; the driver reuses receipt-bound PR81 native 2x1 gold.
// No reference executable or fixture generator is provided by this adapter.
#pragma once
#include "../../hash/tests/dataset_lifecycle_native.hpp"
namespace dataset_capacity_native = prepared_lifecycle_native;
