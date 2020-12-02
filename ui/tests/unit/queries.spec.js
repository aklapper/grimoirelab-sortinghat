import { shallowMount, mount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import IndividualsData from "@/components/IndividualsData";
import IndividualsTable from "@/components/IndividualsTable";
import OrganizationsTable from "@/components/OrganizationsTable";
import Search from "@/components/Search";
import * as Queries from "@/apollo/queries";

Vue.use(Vuetify);

const responseMocked = {
  data: {
    individuals: {
      entities: [
        {
          mk: "172188fd88c1df2dd6d187b6f32cb6aced544aee",
          identities: [{ name: "test name", __typename: "IdentityType" }],
          profile: {
            id: "7",
            name: "test name",
            __typename: "ProfileType"
          },
          __typename: "IndividualType"
        }
      ],
      pageInfo: {
        page: 1,
        pageSize: 10,
        numPages: 1,
        hasNext: false,
        hasPrev: false,
        startIndex: 1,
        endIndex: 1,
        totalResults: 1
      },
      __typename: "IdentityPaginatedType"
    }
  }
};

const paginatedResponse = {
  data: {
    individuals: {
      entities: [
        {
          isLocked: false,
          profile: {
            name: "Test",
            id: "15",
            email: "test6@example.net",
            __typename: "ProfileType"
          },
          identities: [
            {
              name: "Test",
              source: "test",
              email: "test6@example.net",
              uuid: "03b3428eea9c7f29b4f8238b58dc6ecd84bf176a",
              username: "test6",
              __typename: "IdentityType"
            }
          ],
          enrollments: [],
          __typename:"IndividualType"
        }
      ],
      pageInfo: {
        page: 1,
        pageSize: 1,
        numPages: 2,
        totalResults: 2,
        __typename: "PaginationType"
      },
      __typename: "IdentityPaginatedType"
    }
  }
};

const paginatedOrganizations = {
  data: {
    organizations: {
      entities: [
        {
          name: "Test 1",
          enrollments: [
            { id: 1, __typename: "EnrollmentType" },
            { id: 2, __typename: "EnrollmentType" }
          ],
          __typename:	"OrganizationType"
        },
        {
          name: "Test 2",
          enrollments: [
            { id: 3, __typename:	"EnrollmentType" },
            { id: 4, __typename:	"EnrollmentType" }
          ],
          __typename:	"OrganizationType"
        },
        ],
        pageInfo: {
          page: 1,
          pageSize: 10,
          numPages: 1,
          totalResults: 2,
          __typename:	"PaginationType"
        },
        __typename:	"OrganizationPaginatedType"
      }
    }
  };

const countriesMocked = {
  data: {
    countries: {
      entities: [
        { code: "AD", name: "Andorra" },
        { code: "AE", name: "United Arab Emirates" },
        { code: "AF", name: "Afghanistan" },
        { code: "AG", name: "Antigua and Barbuda" },
        { code: "AI", name: "Anguilla" },
        { code: "AL", name: "Albania" },
        { code: "AM", name: "Armenia" }
      ],
      __typename:	"CountryPaginatedType"
    }
  }
};

describe("IndividualsData", () => {
  test("mock query for getIndividuals", async () => {
    const query = jest.fn(() => Promise.resolve(responseMocked));
    const wrapper = shallowMount(IndividualsData, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        getindividuals: {
          query: Queries.getIndividuals.query
        }
      },
      data() {
        return {
          individuals_mocked: null
        }
      }
    });
    let response = await Queries.getIndividuals.query(wrapper.vm.$apollo);
    let individuals_mocked = response.data;
    await wrapper.setData({
      individuals_mocked
    });
    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("getIndividuals with arguments", async () => {
    const getIndividualsSpied = spyOn(Queries.getIndividuals, "query");

    let response = await Queries.getIndividuals.query(undefined, 10, 100);
    expect(getIndividualsSpied).toHaveBeenLastCalledWith(undefined, 10, 100);
  });

  test("getIndividuals with default arguments in the IndividualsData component", async () => {
    const getIndividualsSpied = spyOn(Queries.getIndividuals, "query");
    const query = jest.fn(() => Promise.resolve(responseMocked));
    const wrapper = mount(IndividualsData, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        getindividuals: {
          query: Queries.getIndividuals.query
        }
      }
    });

    expect(getIndividualsSpied).toBeCalled();
    expect(getIndividualsSpied).toHaveBeenCalledWith(wrapper.vm.$apollo, 50);
  });

  test("infinite scroll won't call for more individuals if the page is not at the bottom", async () => {
    const getIndividualsSpied = spyOn(Queries.getIndividuals, "query");
    const query = jest.fn(() => Promise.resolve(responseMocked));
    const wrapper = mount(IndividualsData, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        getindividuals: {
          query: Queries.getIndividuals.query
        }
      }
    });
    wrapper.vm.scroll();

    expect(getIndividualsSpied).toBeCalled();
    expect(getIndividualsSpied).toHaveBeenCalledTimes(1);
  });
});

describe("IndividualsTable", () => {
  const mountFunction = options => {
    return shallowMount(IndividualsTable, {
      Vue,
      propsData: {
        fetchPage: () => {},
        mergeItems: () => {},
        unmergeItems: () => {},
        moveItem: () => {},
        deleteItem: () => {},
        addIdentity: () => {},
        updateProfile: () => {},
        enroll: () => {},
        getCountries: () => {},
        lockIndividual: () => {},
        unlockIndividual: () => {},
        withdraw: () => {}
      },
      ...options
    })
  };

  test("Mock query for getPaginatedIndividuals", async () => {
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: query });
    const response = await Queries.getPaginatedIndividuals(wrapper.vm.$apollo, 1, 1);

    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Searches by term", async () => {
    const querySpy = spyOn(Queries, "getPaginatedIndividuals");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: Queries.getPaginatedIndividuals });
    await wrapper.setData({ filters: { term: "test" } });

    const response = await wrapper.vm.queryIndividuals(1);

    expect(querySpy).toHaveBeenCalledWith(1, 10, { term: "test" });
  });

  test("Searches by lastUpdated", async () => {
    const querySpy = spyOn(Queries, "getPaginatedIndividuals");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: Queries.getPaginatedIndividuals });
    await wrapper.setData({ filters: { lastUpdated: "<2000-01-01T00:00:00.000Z" } });

    const response = await wrapper.vm.queryIndividuals(1);

    expect(querySpy).toHaveBeenCalledWith(1, 10, { lastUpdated: "<2000-01-01T00:00:00.000Z" });
  });

  test("Mock query for getCountries", async () => {
    const query = jest.fn(() => Promise.resolve(countriesMocked));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ getCountries: query });
    const response = await Queries.getCountries(wrapper.vm.$apollo);

    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});

describe("OrganizationsTable", () => {
  test("Mock query for getPaginatedOrganizations", async () => {
    const query = jest.fn(() => Promise.resolve(paginatedOrganizations));
    const wrapper = shallowMount(OrganizationsTable, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        fetchPage: query,
        enroll: () => {},
        addDomain: () => {},
        addOrganization: () => {},
        deleteDomain: () => {}
      }
    });
    const response = await Queries.getPaginatedOrganizations(wrapper.vm.$apollo, 1, 1);

    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});

describe("Search", () => {
  const vuetify = new Vuetify();
  const mountFunction = options => {
    return mount(Search, {
      Vue,
      vuetify,
      ...options,
    })
  };

  test.each([
    ["test"],
    ["term", "test"],
    ["term", " test "],
    ["lastUpdated", "<", "2000", "term", "test"],
    ["term", "test", "lastUpdated", "<", "2000"]
  ])("Given %p parses term", async (...args) => {
    const wrapper = mountFunction({
      data: () => ({ value: args })
    });

    const input = wrapper.find(".v-select__selections > input");
    await input.trigger("change");

    expect(wrapper.vm.searchFilters.term).toBe("test");
  });

  test.each([
    [["lastUpdated", "<", "2000"], "<2000-01-01T00:00:00.000Z"],
    [["lastUpdated", "<", "2000-10-01"], "<2000-10-01T00:00:00.000Z"],
    [["lastUpdated", "<=", "2000-08-10"], "<=2000-08-10T00:00:00.000Z"],
    [["lastUpdated", ">", "2000"], ">2000-01-01T00:00:00.000Z"],
    [["lastUpdated", ">=", "2000-02-03"], ">=2000-02-03T00:00:00.000Z"],
    [
      ["lastUpdated", "range", "2000..2001"],
      "2000-01-01T00:00:00.000Z..2001-01-01T00:00:00.000Z"
    ],
    [["term", "test", "lastUpdated", "<", "2000"], "<2000-01-01T00:00:00.000Z"]
  ])("Given %p parses lastUpdated filter", async (values, expected) => {
    const wrapper = mountFunction({
      data: () => ({ value: values })
    });

    const input = wrapper.find(".v-select__selections > input");
    await input.trigger("change");

    expect(wrapper.vm.searchFilters.lastUpdated).toBe(expected);
  });

  test.each([
    ["lastUpdated", "abc"],
    ["lastUpdated", "<", "abc"],
    ["lastUpdated", "<", "2000-23-01"],
    ["lastUpdated", ">=", "2000-01-49"],
    ["lastUpdated", ">", "@"],
    ["lastUpdated", "range", "2000"],
    ["lastUpdated", "range", "2000-2001"],
    ["lastUpdated", "range", "2001-2000"]
  ])("Given an invalid value renders an error", async (...args) => {
    const wrapper = mountFunction({
      data: () => ({ value: args })
    });

    const input = wrapper.find(".v-select__selections > input");
    await input.trigger("change");
    const errorMessage = wrapper.find(".v-messages__message");

    expect(errorMessage.exists()).toBe(true);
  });
});
