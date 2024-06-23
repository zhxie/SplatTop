import React, { useEffect, useState } from "react";
import Loading from "./misc_components/loading";
import { getBaseApiUrl, buildEndpointWithQueryParams } from "./utils";
import { useTranslation } from "react-i18next";
import useFetchWithCache from "./top500_components/fetch_with_cache";
import WeaponLeaderboardTable from "./leaderboards_components/weapon_leaderboard_table";
import Pagination from "./top500_components/pagination";

const TopWeapons = () => {
  const { t } = useTranslation("main_page");

  const [selectedRegion, setSelectedRegion] = useState("Tentatek");
  const [selectedMode, setSelectedMode] = useState("Splat Zones");
  const [weaponId, setWeaponId] = useState(40);
  const [additionalWeaponId, setAdditionalWeaponId] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 100;

  useEffect(() => {
    document.title = `splat.top - ${selectedRegion} ${selectedMode}`;
  }, [selectedRegion, selectedMode]);

  const apiUrl = getBaseApiUrl();
  const pathUrl = `/api/weapon_leaderboard/${weaponId}`;
  const endpoint = buildEndpointWithQueryParams(apiUrl, pathUrl, {
    mode: selectedMode,
    region: selectedRegion,
  });

  const { data, error, isLoading } = useFetchWithCache(endpoint);

  const players = data
    ? Object.keys(data.players).reduce((acc, key) => {
        data.players[key].forEach((value, index) => {
          if (!acc[index]) acc[index] = {};
          acc[index][key] = value;
        });
        return acc;
      }, [])
    : [];

  if (data) {
    players.forEach((player) => {
      player.weapon_image =
        player.weapon_id === weaponId
          ? data.weapon_image
          : data.additional_weapon_image;
    });
  }

  players.sort((a, b) => {
    return b.max_x_power - a.max_x_power;
  });

  players.forEach((player, index) => {
    player.rank = index + 1;
  });

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = players.slice(indexOfFirstItem, indexOfLastItem);

  const paginate = (pageNumber) => {
    setCurrentPage(pageNumber);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="container mx-auto px-4 py-8 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-4 text-center">{t("title")}</h1>
      <p>
        {t("api_endpoint")}: {endpoint}
      </p>
      <Pagination
        totalItems={players.length}
        itemsPerPage={itemsPerPage}
        currentPage={currentPage}
        onPageChange={paginate}
        isTopOfPage={true}
      />
      {isLoading ? (
        <div className="text-center py-4">
          <Loading text={t("loading")} />
        </div>
      ) : error ? (
        <div className="text-red-500 text-center py-4">{error.message}</div>
      ) : (
        <WeaponLeaderboardTable players={currentItems} />
      )}
      <Pagination
        totalItems={players.length}
        itemsPerPage={itemsPerPage}
        currentPage={currentPage}
        onPageChange={paginate}
        isTopOfPage={false}
      />
    </div>
  );
};

export default TopWeapons;
