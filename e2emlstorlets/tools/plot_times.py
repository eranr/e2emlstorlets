import sys
import numpy as np
import matplotlib.pyplot as plt


def show_plot(e, tr, t, es3, trs3, ts3):
    N = 3
    storlets = (e, tr, t)
    s3 = (es3, trs3, ts3)
    
    ind = np.arange(N)  # the x locations for the groups
    width = 0.35       # the width of the bars
    
    fig, ax = plt.subplots()
    rects1 = ax.bar(ind, storlets, width, color='b')
    rects2 = ax.bar(ind + width, s3, width, color='r')
    
    # add some text for labels, title and axes ticks
    ax.set_ylabel('Time [Seconds]')
    ax.set_title('Swift & Storlets Vs. S3')
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(('Extract', 'Train', 'Swap', 'Recognize'))
    
    ax.legend((rects1[0], rects2[0]), ('Storlets', 'S3'))
    plt.show()


#def autolabel(rects):
#    """
#    Attach a text label above each bar displaying its height
#    """
#    for rect in rects:
#        height = rect.get_height()
#        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
#                '%d' % int(height),
#                ha='center', va='bottom')

#autolabel(rects1)
#autolabel(rects2)

def main(args):
    e = int(args[0])
    tr = int(args[2])
    t = int(args[4])
    es3 = int(args[1])
    trs3 = int(args[3])
    ts3 = int(args[5])
    show_plot(e, tr, s, t, es3, trs3, ss3, ts3)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
