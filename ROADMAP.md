# Roadmap

- [ ] Extract local download check to chromium implementation class
- [x] Fix up browser deps error (eliminate in-package analysis)
- [x] Switch to process group and kill that to catch all chromium children
- [x] Add helpers for running javascript
- [ ] Add helper just for refreshing page
- [ ] Working on better diagnostic information
  - [ ] Explain to user when their system has security restrictions
- [ ] Eliminate synchronous API: it's unused, hard to maintain, and nearly
      worthless
- [ ] Diagnose function should collect a JSON and then print that
- [ ] Allow user to build and send their own JSONS
  - [ ] Get serialization out of the lock
- [ ] Add a websockets extra
- [ ] Support Firefox
- [ ] Support LadyBird (!)
- [ ] Test against multiple docker containers
- [ ] Do browser-rolling tests
- [ ] Do documentation
- [ ] Browser Open/Close Status/PipeCheck status should happen at broker level
  - [ ] Broker should probably be opening browser and running watchdog...
