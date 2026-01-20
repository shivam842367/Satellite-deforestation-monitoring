"use client";

import dynamic from "next/dynamic";

const MapAOIClient = dynamic(() => import("./MapAOIClient"), {
  ssr: false,
});

export default MapAOIClient;
