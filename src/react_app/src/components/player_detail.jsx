import React, { useState, useEffect, Suspense } from "react";
import { useLocation } from "react-router-dom";
import axios from "axios";
import Loading from "./loading";
import { modes } from "./constants";
import { getBaseApiUrl, getBaseWebsocketUrl } from "./utils";
import pako from "pako";
const ChartController = React.lazy(() =>
  import("./player_components/chart_controller")
);
const Aliases = React.lazy(() => import("./player_components/aliases"));
const SeasonResults = React.lazy(() =>
  import("./player_components/season_results")
);
const Achievements = React.lazy(() =>
  import("./player_components/achievements")
);

const DEFAULT_LANGUAGE = "USen";

const PlayerDetail = () => {
  const location = useLocation();
  const player_id = location.pathname.split("/")[2];
  const [data, setData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [weaponTranslations, setWeaponTranslations] = useState(null);
  const [socket, setSocket] = useState(null);
  const [weaponReferenceData, setWeaponReferenceData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      document.title = "splat.top - Player Page";
      const apiUrl = getBaseApiUrl();
      const endpoint = `${apiUrl}/api/player/${player_id}`;
      const translationEndpoint = `${apiUrl}/api/game_translation`;
      const baseWebsocketUrl = getBaseWebsocketUrl();
      const websocketEndpoint = `${baseWebsocketUrl}/ws/player/${player_id}`;

      try {
        const response = await axios.get(endpoint);
        setData(response.data);
        if (response.data && response.data.length > 0) {
          document.title = `splat.top - ${response.data[0].splashtag}`;
        }

        const translationsResponse = await axios.get(translationEndpoint);
        setWeaponTranslations(translationsResponse.data);

        if (socket) {
          socket.close();
        }

        const newSocket = new WebSocket(websocketEndpoint);

        newSocket.onmessage = (event) => {
          if (event.data instanceof Blob) {
            const reader = new FileReader();
            reader.onload = () => {
              const decompressedData = pako.inflate(reader.result, {
                to: "string",
              });
              const newData = JSON.parse(decompressedData);
              setChartData(newData);
            };
            reader.readAsArrayBuffer(event.data);
          } else {
            const newData = JSON.parse(event.data);
            setChartData(newData);
          }
        };

        newSocket.onerror = (event) => {
          setError(new Error("Websocket error"));
        };

        newSocket.onclose = (event) => {
          // Optionally handle the connection close
        };

        setSocket(newSocket);
      } catch (error) {
        setError(error);
      } finally {
        setIsLoading(false);
      }

      const localData = localStorage.getItem("weaponReferenceData");
      if (localData) {
        setWeaponReferenceData(JSON.parse(localData));
      } else {
        try {
          const referenceResponse = await axios.get(
            `${apiUrl}/api/weapon_info`
          );
          setWeaponReferenceData(referenceResponse.data);
          localStorage.setItem(
            "weaponReferenceData",
            JSON.stringify(referenceResponse.data)
          );
        } catch (error) {
          console.error("Error fetching weapon reference data:", error);
        }
      }
    };

    fetchData();

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [player_id]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex flex-col min-h-screen">
      <header className="text-3xl font-bold mb-4 text-center text-white">
        Player Page
      </header>
      <main className="flex-grow container mx-auto px-4 py-8 bg-gray-900 text-white overflow-auto">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <Loading text="Loading page..." />
          </div>
        ) : error ? (
          <div className="text-red-500 text-center">{error.message}</div>
        ) : (
          <Suspense fallback={<Loading text="Loading components..." />}>
            {data && data.length > 0 ? (
              <div className="flex flex-col md:flex-row">
                <div className="md:w-2/5 md:pr-8">
                  <Aliases data={data} />
                  {chartData ? (
                    <>
                      <SeasonResults
                        data={chartData}
                        weaponReferenceData={weaponReferenceData}
                      />
                      <Achievements data={chartData} />
                    </>
                  ) : (
                    <Loading text="Loading season results..." />
                  )}
                </div>
                <div className="md:w-3/5 mt-8 md:mt-0">
                  {chartData ? (
                    <ChartController
                      data={chartData}
                      modes={modes}
                      weaponTranslations={weaponTranslations[DEFAULT_LANGUAGE]}
                      weaponReferenceData={weaponReferenceData}
                    />
                  ) : (
                    <Loading text={"Loading chart..."} />
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center">No data available</div>
            )}
          </Suspense>
        )}
      </main>
    </div>
  );
};

export default PlayerDetail;