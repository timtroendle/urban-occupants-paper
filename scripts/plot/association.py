import click
import matplotlib.pyplot as plt
import pandas as pd


@click.command()
@click.argument('path_to_ts_association')
@click.argument('path_to_plot')
def association_plots(path_to_ts_association, path_to_plot):
    ts_corr_1d = pd.read_pickle(path_to_ts_association)
    ax = ts_corr_1d.plot(figsize=(14, 7))
    _ = plt.title("Cramer's phi for each time step of people model")
    _ = plt.ylabel("Cramer's phi")
    _ = plt.xlabel("time step")
    plt.savefig(path_to_plot, dpi=300)


if __name__ == '__main__':
    association_plots()
