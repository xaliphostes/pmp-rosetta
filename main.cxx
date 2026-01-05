// ============================================================================
// Custom Binding Generator for the PMP Project
// 
// This generator compile PMP project and calls the Rosetta
// registration function BEFORE generating bindings, so the generator can
// discover all registered classes.
// ============================================================================

#include <rosetta/extensions/generators/common/BindingGeneratorLib.h>
#include "pmp_registration.h"

int main(int argc, char* argv[]) {
    // IMPORTANT: Call registration BEFORE running the generator
    // This populates rosetta::Registry::instance() with class metadata
    pmp_rosetta::register_all();
    
    // Now run the binding generator
    // It will query the registry and find Point, Triangle, Surface, Model
    return BindingGeneratorLib::run(argc, argv);
}
