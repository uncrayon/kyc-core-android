plugins {
    id("com.android.application") version "8.10.1" apply false
    id("org.jetbrains.kotlin.android") version "1.9.10" apply false
    id("com.android.library") version "8.10.1" apply false
}

task<Delete>("clean") {
    delete(rootProject.buildDir)
}