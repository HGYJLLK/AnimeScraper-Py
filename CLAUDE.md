# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Animeko is a multiplatform anime tracking and streaming application built with Kotlin Multiplatform and Compose Multiplatform. It supports Android, iOS, Windows, macOS, and Linux platforms.

## Development Commands

### Build Commands
- `./gradlew build` - Build the entire project
- `./gradlew :app:desktop:run` - Run desktop application
- `./gradlew :app:android:assembleDebug` - Build Android debug APK
- `./gradlew :app:android:assembleRelease` - Build Android release APK
- `./gradlew createReleaseDistributable` - Build desktop application for distribution
- `./gradlew runReleaseDistributable` - Run optimized desktop release version

### Test Commands  
- `./gradlew test` - Run all tests
- `./gradlew :module:test` - Run tests for specific module
- `./gradlew testDebugUnitTest` - Run Android unit tests
- `./gradlew check` - Run all checks including tests and lint

### Gradle Tasks
- `./gradlew downloadAllDependencies` - Download all dependencies
- `./gradlew clean` - Clean build artifacts

## Architecture Overview

### Multiplatform Structure
The project uses Kotlin Multiplatform with these main target groups:
- `commonMain` - Shared code for all platforms
- `androidMain` - Android-specific implementations
- `desktopMain` - Desktop (JVM) implementations  
- `iosMain` - iOS implementations
- `skikoMain` - Skiko-based platforms (desktop graphics)

### Core Modules

#### Data Sources (`/datasource`)
- **Bangumi** - Integration with Bangumi.tv for anime metadata
- **BT Sources** - BitTorrent sources (DMHY, Mikan)
- **Web Sources** - Web scraping-based video sources
- **Jellyfin/Emby** - Media server integration
- **Ikaros** - Ikaros media server integration

#### Application Layers (`/app/shared`)
- **app-data** - Data layer, repositories, and use cases
- **app-platform** - Platform-specific implementations
- **application** - Application layer coordination

#### UI Modules
- **ui-foundation** - Base UI components and theming
- **ui-subject** - Anime subject/series pages
- **ui-episode** - Episode viewing interfaces
- **ui-exploration** - Browse and search interfaces
- **ui-settings** - Application settings

#### Utilities (`/utils`)
- **ktor-client** - HTTP client configuration
- **coroutines** - Coroutine utilities and extensions
- **platform** - Platform detection and abstractions

## Architecture Details

### Video Source Scraping Architecture

#### Web-based Data Sources
The web scraping functionality for video sites is located in:

- **Primary Engine**: `/app/shared/app-data/src/commonMain/kotlin/domain/mediasource/web/`
  - `SelectorMediaSource.kt:101-298` - Main CSS selector-based scraping implementation
  - `SelectorMediaSourceEngine.kt:90-432` - Core scraping engine using CSS selectors and JSoup-style parsing

- **Base Classes**: `/datasource/web/web-base/src/`
  - `WebMediaSource.kt:1-5` - Base class for web-based sources
  - `TreeStepWebMediaSource.kt:37-152` - Three-step scraping pattern (search → subject → episodes)

### Scraping Process
1. **Subject Search**: Parse search results using CSS selectors to find anime subjects
2. **Episode Discovery**: Navigate to subject pages and extract episode lists  
3. **Video Link Extraction**: Extract actual video URLs from episode pages
4. **Video Matching**: Match video URLs using regex patterns and WebView integration

### Configuration System
- Uses `SelectorSearchConfig` for configuring CSS selectors, search URLs, filters
- Supports custom headers, cookies, and request intervals for scraping
- Platform-specific player support (VLC, ExoPlayer, AVKit)

### Key Technologies
- **JSoup-style parsing** via custom XML utils (`/utils/xml/`)
- **Ktor HTTP client** for requests (`/utils/ktor-client/`)  
- **CSS Selector engine** for content extraction
- **WebView integration** for JavaScript-heavy sites

### BitTorrent Architecture

#### Torrent Engine (`/torrent`)
- **anitorrent** - Native BitTorrent implementation using libtorrent
  - `AnitorrentTorrentDownloader.kt` - Main downloader implementation
  - `TorrentManagerSession.kt` - Session management for torrent operations
  - Platform-specific implementations for JVM and Native targets
- **api** - Common torrent API abstractions
  - `TorrentDownloader.kt` - Core downloader interface
  - `TorrentInput.kt` - Streaming input for torrents
  - `PieceList.kt` - Piece-based download management

## Development Setup

### Requirements
- JDK 21 (JetBrains Runtime recommended)
- Android SDK (API 27-35)
- Gradle 8.x with configuration cache enabled

### Platform-Specific Setup
- **Android**: Standard Android SDK setup
- **Desktop**: VLC libraries (included in appResources)
- **iOS**: Xcode and CocoaPods required

### Memory Configuration
The project requires significant memory for builds:
- Gradle: `-Xmx6g`
- Kotlin daemon: `-Xmx4096M`

## Testing and Debugging

### Running Tests
- Unit tests: `./gradlew test`
- Android instrumented tests: `./gradlew connectedAndroidTest`
- Specific module tests: `./gradlew :datasource:api:test`

### Running Debug Applications
- **Desktop Hot Reload** (Recommended): Use "Run Desktop (Hot Reload)" configuration in IDE
- **Android Debug**: Use "app.android" configuration in IDE
- **Desktop Normal**: Use "Run Desktop (Normal)" configuration in IDE

### Performance Notes
- Debug builds have significantly lower performance than release builds
- Use release builds (`runReleaseDistributable`) for performance testing
- Desktop hot reload enables real-time code updates without restart