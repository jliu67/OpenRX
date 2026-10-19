// SPDX-License-Identifier: BSD-3-Clause
// Keep accepted native main and every reference body unchanged. A separate
// role selects retained cache0 and exports direct native item assertion rows.
// The admitted driver binds argv to2programsx1iteration v2 and sets both
// RX_PREPARED_CACHE_ROOT and RX_PREPARED_REFERENCE_OUTPUT to fresh bound paths.
#include "dataset_lifecycle_native.hpp"
namespace {
struct PreparedReferenceRole {
    PreparedReferenceRole() { prepared_lifecycle_native::reference_role = true; }
} prepared_reference_role;
}
#define lifecycle_native prepared_lifecycle_native
#include "lifecycle_reference.cpp"
#undef lifecycle_native
